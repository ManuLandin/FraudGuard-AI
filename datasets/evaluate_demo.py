"""Evalúa la partición temporal sin modificar etiquetas ni el modelo de la plataforma."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.ml.evaluation import evaluate
from app.ml.model import train,infer
from app.services.csv_import import parse_csv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=ROOT/'datasets/fraudguard_demo_1000.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evaluation/demo_1000')
    args=parser.parse_args()
    data=args.csv.read_bytes()
    manifest=json.loads(args.csv.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(data).hexdigest()!=manifest['sha256']:
        raise ValueError('El CSV no coincide con su manifiesto. Regenera los datos antes de evaluar.')
    frame=pd.DataFrame(parse_csv(data,10000))
    cutoff=pd.Timestamp(manifest['split_cutoff'])
    reference=frame.loc[pd.to_datetime(frame.timestamp,utc=True)<cutoff].reset_index(drop=True)
    test=frame.loc[pd.to_datetime(frame.timestamp,utc=True)>=cutoff].reset_index(drop=True)
    report=evaluate(reference,test)
    model=train(reference)
    predictions=infer(model,test)
    truth=test.label.astype(int)
    predicted=predictions.is_anomaly.astype(int)
    errors=test.copy().rename(columns={'label':'reference_is_anomaly'})
    errors['anomaly_kind']=errors.transaction_id.map(manifest['anomaly_kinds'])
    for column in predictions:errors['predicted_is_anomaly' if column=='is_anomaly' else column]=predictions[column]
    errors['error_type']=['TP' if y and p else 'FN' if y else 'FP' if p else 'TN' for y,p in zip(truth,predicted)]
    report.update(dataset_sha256=manifest['sha256'],generator_seed=manifest['random_state'],split_cutoff=manifest['split_cutoff'],false_positive_ids=errors.loc[errors.error_type=='FP','transaction_id'].tolist(),false_negative_ids=errors.loc[errors.error_type=='FN','transaction_id'].tolist(),per_family={name:{'rows':len(group),'flagged':int(group.predicted_is_anomaly.sum()),'reference_positive':int(group.reference_is_anomaly.sum())} for name,group in errors.groupby('anomaly_kind')})
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    errors.to_csv(args.output/'predictions.csv',index=False,float_format='%.8f')
    errors.loc[errors.error_type=='FP'].to_csv(args.output/'false_positives.csv',index=False)
    errors.loc[errors.error_type=='FN'].to_csv(args.output/'false_negatives.csv',index=False)
    print(json.dumps({key:report[key] for key in ['fit_rows','calibration_rows','test_rows','positive_labels','isolation_forest','amount_baseline']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
