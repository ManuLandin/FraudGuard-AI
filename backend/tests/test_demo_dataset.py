import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.services.csv_import import parse_csv

ROOT=Path(__file__).resolve().parents[2]
def generator():
    spec=importlib.util.spec_from_file_location("fraudguard_generator", ROOT/"datasets/generate_demo.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_generation_schema_counts_dates_and_reproducibility():
    g=generator(); first=g.generate_demo(); second=g.generate_demo(random_state=42)
    pd.testing.assert_frame_equal(first,second)
    assert first.to_csv(index=False)==second.to_csv(index=False)
    assert list(first.columns)==['transaction_id','user_id','amount','timestamp','transaction_type','merchant_category','location','is_anomaly']
    assert len(first)==1000 and first.is_anomaly.value_counts().to_dict()=={0:900,1:100}
    assert first.transaction_id.is_unique
    assert np.isfinite(first.amount).all() and (first.amount>0).all()
    stamps=pd.to_datetime(first.timestamp,utc=True)
    assert stamps.max()-stamps.min() < pd.Timedelta(days=90)
    assert stamps.min() >= pd.Timestamp('2026-08-01T00:00:00-06:00')
    assert stamps.max() < pd.Timestamp('2026-10-30T00:00:00-06:00')
    assert set(first.transaction_type)=={'compra','transferencia','retiro','pago'}
    assert first.loc[first.is_anomaly==1,'amount'].median() < first.loc[first.is_anomaly==0,'amount'].max()
    assert not first.equals(g.generate_demo(random_state=43))

def test_checked_in_csv_matches_generator_and_imports(tmp_path):
    g=generator(); expected=g.csv_bytes(g.generate_demo())
    assert (ROOT/'datasets/fraudguard_demo_1000.csv').read_bytes()==expected
    with TestClient(create_app(Settings(database_url='sqlite:///'+(tmp_path/'db.sqlite').as_posix(),_env_file=None))) as client:
        response=client.post('/api/transactions/upload',files={'file':('demo.csv',expected,'text/csv')})
        assert response.status_code==201
        batch=response.json()['batch_id']
        page=client.get('/api/transactions',params={'batch_id':batch,'page_size':100}).json()
        assert page['total']==1000
        assert all(t['user_id']==t['account_id'] and t['transaction_type'] and t['location'] for t in page['items'])
        assert all(t['anomaly_score'] is None for t in page['items'])

def test_alias_labels_are_not_features_and_are_validated():
    from app.ml.features import TransactionFeatures
    g=generator(); frame=g.generate_demo(); parsed=pd.DataFrame(parse_csv(g.csv_bytes(frame),10000))
    features=TransactionFeatures().fit(parsed)
    altered=parsed.assign(label=1-parsed.label)
    np.testing.assert_array_equal(features.transform(parsed),features.transform(altered))
    invalid=frame.copy();invalid.loc[0,'is_anomaly']=2
    with pytest.raises(HTTPException):parse_csv(g.csv_bytes(invalid),10000)
    invalid=frame.copy();invalid.loc[0,'transaction_type']='unknown'
    with pytest.raises(HTTPException):parse_csv(g.csv_bytes(invalid),10000)


def test_anomaly_families_include_subtle_and_burst_behaviour():
    frame=generator().generate_demo()
    kinds=pd.Series(frame.transaction_id.map(frame.attrs['anomaly_kinds']).to_numpy())
    assert kinds.value_counts().to_dict()=={'normal':900,'monto_alto':20,'horario_inusual':20,'cambio_patron':20,'combinada':20,'rafaga':20}
    threshold=frame.loc[frame.is_anomaly==0,'amount'].quantile(.95)
    assert (frame.loc[frame.is_anomaly==1,'amount'] <= threshold).sum() >= 30
    bursts=frame.loc[kinds=='rafaga'].copy()
    bursts['date']=pd.to_datetime(bursts.timestamp,utc=True)
    diffs=bursts.sort_values(['user_id','date']).groupby('user_id')['date'].diff().dt.total_seconds()
    assert diffs.between(15,60).sum() >= 16


def test_cli_outputs_identical_bytes_and_temporal_partitions(tmp_path):
    import subprocess,sys,json
    first,second=tmp_path/'first.csv',tmp_path/'second.csv'
    for path in [first,second]:
        subprocess.run([sys.executable,str(ROOT/'datasets/generate_demo.py'),'--output',str(path)],check=True,capture_output=True,timeout=60)
    assert first.read_bytes()==second.read_bytes()
    assert first.with_suffix('.manifest.json').read_bytes()==second.with_suffix('.manifest.json').read_bytes()
    reference=pd.read_csv(tmp_path/'first_reference.csv')
    test=pd.read_csv(tmp_path/'first_test.csv')
    assert len(reference)+len(test)==1000
    assert pd.to_datetime(reference.timestamp,utc=True).max() < pd.to_datetime(test.timestamp,utc=True).min()
    assert not set(reference.transaction_id)&set(test.transaction_id)
    assert reference.is_anomaly.sum()+test.is_anomaly.sum()==100
    manifest=json.loads(first.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    assert manifest['random_state']==42


def test_conflicting_aliases_cannot_silently_override_labels():
    frame=generator().generate_demo()
    frame['label']=1-frame.is_anomaly
    with pytest.raises(HTTPException):parse_csv(frame.to_csv(index=False).encode(),10000)


def test_demo_temporal_split_trains_and_analyzes_through_api(tmp_path):
    with TestClient(create_app(Settings(database_url='sqlite:///'+(tmp_path/'demo.sqlite').as_posix(),model_path=tmp_path/'model.joblib',_env_file=None))) as client:
        batches=[]
        for part in ['reference','test']:
            path=ROOT/f'datasets/fraudguard_demo_1000_{part}.csv'
            response=client.post('/api/transactions/upload',files={'file':(path.name,path.read_bytes(),'text/csv')})
            assert response.status_code==201
            batches.append(response.json()['batch_id'])
        assert client.post('/api/ml/train',json={'batch_id':batches[0]}).status_code==200
        analysis=client.post('/api/ml/analyze',json={'batch_id':batches[1]})
        assert analysis.status_code==200 and analysis.json()['analyzed']==291
        summary=client.get('/api/dashboard/summary',params={'batch_id':batches[1]}).json()
        assert summary['analyzed']==291 and summary['pending']==0
        row=client.get('/api/transactions',params={'batch_id':batches[1],'page_size':1}).json()['items'][0]
        assert row['merchant_category'] and row['is_anomaly'] in [0,1]
        assert row['anomaly_score'] is not None
