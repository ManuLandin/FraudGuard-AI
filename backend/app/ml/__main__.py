"""Ejecutar desde backend: python -m app.ml train|analyze ..."""
import argparse
import json
from pathlib import Path
import pandas as pd
from fastapi import HTTPException
from app.core.config import Settings
from app.ml.model import train, infer, save_model, load_model
from app.services.csv_import import parse_csv


def main():
    parser = argparse.ArgumentParser(description="Anomalías en datos sintéticos; no confirma fraudes.")
    parser.add_argument("action", choices=["train", "analyze"])
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True, help="Artefacto local de confianza, nunca un archivo recibido de terceros.")
    parser.add_argument("--output", type=Path, help="Archivo JSON de resultados (obligatorio para analyze).")
    args = parser.parse_args()
    if args.action == "analyze" and args.output is None:
        parser.error("analyze requiere --output")
    if args.csv.resolve() == args.model.resolve() or (args.output and args.output.resolve() in (args.csv.resolve(), args.model.resolve())):
        parser.error("Los archivos de entrada, modelo y salida deben ser distintos.")
    try:
        settings = Settings()
        with args.csv.open("rb") as source:
            data = source.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise ValueError("CSV demasiado grande.")
        frame = pd.DataFrame(parse_csv(data, settings.max_csv_rows))
        if args.action == "train":
            model = train(frame)
            save_model(model, args.model)
            print(json.dumps({"fit_rows": model.fit_rows, "calibration_rows": model.calibration_rows, "model": str(args.model)}, ensure_ascii=False))
        else:
            model = load_model(args.model)
            results = infer(model, frame)
            results.insert(0, "transaction_id", frame["transaction_id"].to_numpy())
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"notice": "Anomalías orientativas; no son fraudes confirmados ni probabilidades de fraude.", "model_created_at": model.created_at, "results": results.to_dict(orient="records")}, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
            print(f"Resultados guardados en {args.output}")
    except (ValueError, OSError, HTTPException) as exc:
        parser.exit(1, f"Error: {getattr(exc, 'detail', str(exc))}\n")

if __name__ == "__main__":
    main()
