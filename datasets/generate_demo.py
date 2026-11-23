"""Dataset 100% ficticio de un pequeño negocio mexicano. No representa fraude."""
import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd

COLUMNS=['transaction_id','user_id','amount','timestamp','transaction_type','merchant_category','location','is_anomaly']
START=datetime(2026,8,1,tzinfo=timezone(timedelta(hours=-6)))
CATEGORIES=['abarrotes','papeleria','insumos_cafeteria','transporte','servicios','equipo_oficina','mantenimiento','publicidad']
LOCATIONS=['Zona Centro Ficticia','Zona Norte Ficticia','Zona Sur Ficticia','Zona Oriente Ficticia']
TYPES=['compra','transferencia','retiro','pago']


def generate_demo(random_state: int = 42) -> pd.DataFrame:
    rng=np.random.default_rng(random_state)
    profiles=[]
    for i in range(18):
        profiles.append(dict(user=f'usuario_demo_{i+1:02d}', median=float(rng.uniform(95,680)), categories=rng.choice(CATEGORIES,2,replace=False).tolist(), location=str(rng.choice(LOCATIONS)), hour=float(rng.uniform(10,17))))
    days=np.arange(90)
    weights=np.array([.4 if (START+timedelta(days=int(d))).weekday()==6 else .8 if (START+timedelta(days=int(d))).weekday()==5 else 1. for d in days]);weights/=weights.sum()
    rows=[]; normal_slots={}
    def typical(profile):
        amount=float(np.clip(rng.lognormal(np.log(profile['median']),.46),25,4500))
        return dict(user_id=profile['user'],amount=round(amount,2),transaction_type=str(rng.choice(TYPES,p=[.58,.14,.08,.20])),merchant_category=str(rng.choice(profile['categories'],p=[.78,.22])),location=profile['location'] if rng.random()<.91 else str(rng.choice(LOCATIONS)))
    def moment(profile,day,night=False):
        hour=int(rng.integers(0,6)) if night else int(np.clip(rng.normal(profile['hour'],2),8,20))
        return START+timedelta(days=int(day),hours=hour,minutes=int(rng.integers(0,60)),seconds=int(rng.integers(0,60)))
    def add(row,stamp,kind):
        rows.append({**row,'timestamp':stamp.isoformat(),'is_anomaly':int(kind!='normal'),'_kind':kind})
    # Espaciado normal por usuario; distribución y preferencias con variación natural.
    for _ in range(900):
        profile=profiles[int(rng.integers(len(profiles)))]
        for attempt in range(500):
            day=int(rng.choice(days,p=weights)); stamp=moment(profile,day)
            previous=normal_slots.setdefault(profile['user'],[])
            if all(abs((stamp-t).total_seconds())>=2700 for t in previous):
                previous.append(stamp);break
        else: raise RuntimeError('No fue posible separar operaciones normales.')
        add(typical(profile),stamp,'normal')
    for kind in ['monto_alto','horario_inusual','cambio_patron','combinada']:
        for _ in range(20):
            profile=profiles[int(rng.integers(len(profiles)))]; row=typical(profile)
            day=int(rng.choice(days,p=weights));stamp=moment(profile,day,night=kind in ['horario_inusual','combinada'])
            if kind=='monto_alto':row['amount']=round(row['amount']*float(rng.uniform(9,18)),2)
            if kind in ['cambio_patron','combinada']:
                row['merchant_category']=str(rng.choice([c for c in CATEGORIES if c not in profile['categories']]))
                row['transaction_type']=str(rng.choice(['retiro','transferencia']))
                row['location']=str(rng.choice([l for l in LOCATIONS if l!=profile['location']]))
            if kind=='combinada':row['amount']=round(row['amount']*float(rng.uniform(3,7)),2)
            add(row,stamp,kind)
    # Cuatro ráfagas de cinco operaciones, de monto/horario habituales.
    for _ in range(4):
        profile=profiles[int(rng.integers(len(profiles)))];stamp=moment(profile,int(rng.choice(days,p=weights)))
        for _ in range(5):
            add(typical(profile),stamp,'rafaga');stamp+=timedelta(seconds=int(rng.integers(15,61)))
    # IDs sin prefijos de clase; la etiqueta no se puede deducir del orden de IDs.
    for row,identifier in zip(rows,rng.permutation(np.arange(1,1001))):row['transaction_id']=f'FG-DEMO-{identifier:06d}'
    frame=pd.DataFrame(rows).sort_values(['timestamp','transaction_id'],kind='stable').reset_index(drop=True)
    kinds=dict(zip(frame.transaction_id,frame['_kind']))
    frame=frame[COLUMNS]
    frame.attrs['anomaly_kinds']=kinds
    return frame


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False,float_format='%.2f',lineterminator='\n').encode('utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('fraudguard_demo_1000.csv'))
    args=parser.parse_args();frame=generate_demo(args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(csv_bytes(frame))
    # Corte fijo al día 63, sin consultar etiquetas ni forzar proporciones por partición.
    cutoff=START+timedelta(days=63)
    dates=pd.to_datetime(frame.timestamp,utc=True)
    reference=frame.loc[dates < pd.Timestamp(cutoff)]
    test=frame.loc[dates >= pd.Timestamp(cutoff)]
    for suffix,part in [('reference',reference),('test',test)]:
        args.output.with_name(args.output.stem+'_'+suffix+'.csv').write_bytes(csv_bytes(part))
    manifest={'synthetic':True,'random_state':args.seed,'start':START.isoformat(),'end_exclusive':(START+timedelta(days=90)).isoformat(),'split_cutoff':cutoff.isoformat(),'rows':len(frame),'normal':900,'anomalous':100,'sha256':hashlib.sha256(csv_bytes(frame)).hexdigest(),'anomaly_kinds':frame.attrs['anomaly_kinds']}
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{args.output}: {len(frame)} filas, {int(frame.is_anomaly.sum())} anomalías sintéticas, semilla {args.seed}.')

if __name__=='__main__': main()
