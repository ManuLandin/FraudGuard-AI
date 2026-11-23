"""Evaluación temporal separada; nunca ajusta umbrales con etiquetas de prueba."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from app.ml.features import validate_frame
from app.ml.model import train, infer
from app.services.csv_import import parse_csv


def metrics(labels, predicted, ranking):
    if not len(labels):
        return dict(precision=None, recall=None, f1=None, roc_auc=None, average_precision=None, confusion_matrix=None)
    matrix=confusion_matrix(labels,predicted,labels=[0,1])
    tn,fp,fn,tp=map(int,matrix.ravel())
    both=len(np.unique(labels)) == 2
    return {"precision":tp/(tp+fp) if tp+fp else None, "recall":tp/(tp+fn) if tp+fn else None, "f1":2*tp/(2*tp+fp+fn) if tp+fn and 2*tp+fp+fn else None, "roc_auc":float(roc_auc_score(labels,ranking)) if both else None, "average_precision":float(average_precision_score(labels,ranking)) if both else None, "confusion_matrix":matrix.tolist()}


def evaluate(reference: pd.DataFrame, test: pd.DataFrame) -> dict:
    fit_data=validate_frame(reference)
    test_data=validate_frame(test)
    if test_data.timestamp.min() <= fit_data.timestamp.max():
        raise ValueError("La evaluación debe ser estrictamente posterior a toda la referencia de ajuste/calibración.")
    # train aplica su división temporal interna sin usar etiquetas.
    model=train(reference)
    result=infer(model,test)
    labels=test.get("label",pd.Series([None]*len(test),index=test.index))
    available=labels.notna().to_numpy()
    selected=labels.loc[labels.notna()]
    if not selected.isin([0,1]).all():
        raise ValueError("Las etiquetas disponibles deben ser 0 o 1.")
    y=selected.to_numpy(dtype=int)
    # Línea base fijada solo en filas de ajuste: percentil 99 del monto.
    ordered=fit_data.sort_values("timestamp",kind="stable")
    baseline_fit=ordered.loc[ordered.timestamp < pd.Timestamp(model.calibration_start)]
    threshold=float(np.quantile(baseline_fit.amount_cents,.99))
    amounts=test_data.amount_cents.to_numpy()
    return {"notice":"Evaluación de anomalías sintéticas; no confirma fraudes ni generaliza a banca real.","reference_rows":len(reference),"fit_rows":model.fit_rows,"calibration_rows":model.calibration_rows,"test_rows":len(test),"labeled_rows":len(y),"unlabeled_rows":int((~available).sum()),"positive_labels":int(y.sum()),"fit_end":model.fit_end,"calibration_start":model.calibration_start,"reference_end":fit_data.timestamp.max().isoformat(),"test_start":test_data.timestamp.min().isoformat(),"seed":model.seed,"library_versions":model.library_versions,"anomaly_threshold":99,"baseline_threshold_cents":threshold,"matrix_order":"[[TN, FP], [FN, TP]]; clase positiva=atípico sintético","ranking_score":"Isolation Forest: -score_samples; línea base: amount_cents","isolation_forest":metrics(y,result.is_anomaly.to_numpy()[available],result.raw_anomaly_score.to_numpy()[available]),"amount_baseline":metrics(y,amounts[available]>threshold,amounts[available])}


def main():
    parser=argparse.ArgumentParser(description="Evaluación temporal de anomalías, no fraude.")
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--test",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve() in (args.reference.resolve(),args.test.resolve()):
        parser.error("El informe no puede sobrescribir datos de entrada.")
    def read(path):
        with path.open("rb") as source: data=source.read(5*1024*1024+1)
        if len(data)>5*1024*1024: raise ValueError("Archivo mayor de 5 MiB.")
        return pd.DataFrame(parse_csv(data,10000))
    report=evaluate(read(args.reference),read(args.test))
    report["input_sha256"]={"reference":hashlib.sha256(args.reference.read_bytes()).hexdigest(),"test":hashlib.sha256(args.test.read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
