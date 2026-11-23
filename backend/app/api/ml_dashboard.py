from collections import defaultdict
from datetime import datetime, timezone
import threading
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.api.transactions import DB
from app.schemas.dashboard import DashboardSummary, ModelStatus, TrainingResult, AnalysisResponse
from app.ml.model import train, infer, load_model, save_model
from app.models.transaction import AnalysisResult, ImportBatch, Transaction

router = APIRouter()
# Serializa entrenamiento/análisis en el único proceso local del MVP.
model_lock = threading.Lock()

class BatchInput(BaseModel):
    batch_id: int = Field(ge=1, le=9223372036854775807)

def rows_for_batch(session, batch_id):
    if session.get(ImportBatch, batch_id) is None:
        raise HTTPException(404, "Lote no encontrado.")
    return session.scalars(select(Transaction).where(Transaction.batch_id == batch_id).order_by(Transaction.id)).all()

def frame(rows):
    return pd.DataFrame([{"amount_cents": t.amount_cents, "timestamp": t.timestamp} for t in rows])

@router.get("/api/ml/status", response_model=ModelStatus)
def status(request: Request):
    with model_lock:
        try:
            model = load_model(request.app.state.settings.model_path)
            return {"ready": True, "created_at": model.created_at, "fit_rows": model.fit_rows, "calibration_rows": model.calibration_rows}
        except Exception:
            return {"ready": False, "message": "Modelo no disponible. Entrena con un lote de referencia de al menos 80 filas."}

@router.post("/api/ml/train", response_model=TrainingResult)
def train_batch(body: BatchInput, request: Request, session: DB):
    rows = rows_for_batch(session, body.batch_id)
    with model_lock:
        try:
            model = train(frame(rows))
            save_model(model, request.app.state.settings.model_path)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        except OSError:
            raise HTTPException(503, "No se pudo guardar el modelo local.") from None
    return {"created_at": model.created_at, "fit_rows": model.fit_rows, "calibration_rows": model.calibration_rows}

@router.post("/api/ml/analyze", response_model=AnalysisResponse)
def analyze_batch(body: BatchInput, request: Request, session: DB):
    rows = rows_for_batch(session, body.batch_id)
    with model_lock:
        try:
            model = load_model(request.app.state.settings.model_path)
        except Exception:
            raise HTTPException(409, "No hay un modelo compatible. Entrena un lote de referencia primero.") from None
        result = infer(model, frame(rows))
        for row, scored in zip(rows, result.to_dict(orient="records")):
            session.merge(AnalysisResult(transaction_id=row.id, anomaly_score=float(scored["anomaly_score"]), raw_score=float(scored["raw_anomaly_score"]), risk_level=scored["risk_level"], model_created_at=model.created_at, analyzed_at=datetime.now(timezone.utc).isoformat()))
        session.commit()
    return {"analyzed": len(rows), "model_created_at": model.created_at}

@router.get("/api/dashboard/summary", response_model=DashboardSummary)
def summary(session: DB, batch_id: int | None = Query(None, ge=1, le=9223372036854775807)):
    statement = select(Transaction)
    if batch_id is not None:
        statement = statement.where(Transaction.batch_id == batch_id)
    rows = session.scalars(statement).all()
    daily, histogram = defaultdict(lambda: {"count": 0, "amount_cents": 0}), [0]*5
    distribution = {"bajo": 0, "medio": 0, "alto": 0, "pendiente": 0}
    for t in rows:
        day = t.timestamp[:10]
        daily[day]["count"] += 1
        daily[day]["amount_cents"] += t.amount_cents
        distribution[t.risk_level or "pendiente"] += 1
        index = next((i for i, limit in enumerate([10000,100000,1000000,10000000]) if t.amount_cents < limit), 4)
        histogram[index] += 1
    total, analyzed = len(rows), len(rows)-distribution["pendiente"]
    return {"total": total, "analyzed": analyzed, "pending": total-analyzed, "anomalies": distribution["alto"], "anomaly_percentage": 100*distribution["alto"]/analyzed if analyzed else None, "amount_cents": str(sum(t.amount_cents for t in rows)), "distribution": [{"name":k,"count":v} for k,v in distribution.items()], "daily": [{"date":d,"count":v["count"],"amount_cents":str(v["amount_cents"])} for d,v in sorted(daily.items())], "amount_distribution": [{"name":n,"count":v} for n,v in zip(["<100","100–999","1 mil–9 mil","10 mil–99 mil","≥100 mil"],histogram)]}
