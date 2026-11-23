from pathlib import PurePosixPath
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, Path as PathParam
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.transaction import ImportBatch, Transaction, AnalysisResult, TransactionContext
from app.schemas.transaction import TransactionOut, TransactionPage, UploadResult
from app.services.csv_import import parse_csv
from app.schemas.dashboard import BatchOut

router = APIRouter(prefix="/api/transactions", tags=["Transacciones"])

def get_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session

DB = Annotated[Session, Depends(get_session)]

@router.post("/upload", response_model=UploadResult, status_code=201)
def upload(request: Request, session: DB, file: UploadFile = File(...)):
    settings = request.app.state.settings
    try:
        filename = PurePosixPath((file.filename or "").replace("\\", "/")).name
        if not filename.lower().endswith(".csv") or len(filename) > 255:
            raise HTTPException(415, "Selecciona un archivo con extensión .csv y nombre de hasta 255 caracteres.")
        data = file.file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, "El archivo excede el tamaño permitido.")
        rows = parse_csv(data, settings.max_csv_rows)
        try:
            with session.begin():
                batch = ImportBatch(filename=filename, row_count=len(rows))
                session.add(batch)
                session.flush()
                metadata_keys = {"transaction_type", "merchant_category", "location"}
                transactions = [Transaction(batch_id=batch.id, **{key:value for key,value in row.items() if key not in metadata_keys}) for row in rows]
                session.add_all(transactions)
                session.flush()
                for transaction, row in zip(transactions, rows):
                    metadata = {key: row[key] for key in metadata_keys if key in row}
                    if metadata:
                        transaction.context = TransactionContext(**metadata)
                session.flush()
                result = UploadResult(batch_id=batch.id, filename=filename, row_count=len(rows), preview=[TransactionOut.model_validate(t) for t in transactions[:5]])
            return result
        except SQLAlchemyError:
            raise HTTPException(503, "No se pudo guardar el lote. Vuelve a intentarlo.") from None
    finally:
        file.file.close()

@router.get("/batches", response_model=list[BatchOut])
def list_batches(session: DB):
    return [{"id": b.id, "filename": b.filename, "row_count": b.row_count, "created_at": b.created_at} for b in session.scalars(select(ImportBatch).order_by(ImportBatch.id.desc()))]

@router.get("", response_model=TransactionPage)
def list_transactions(session: DB, page: int = Query(1, ge=1, le=1000000000), page_size: int = Query(25, ge=1, le=100), batch_id: int | None = Query(None, ge=1, le=9223372036854775807), search: str = Query("", max_length=100), risk_level: Literal["bajo", "medio", "alto", "pendiente"] | None = None):
    filters = []
    if batch_id is not None:
        filters.append(Transaction.batch_id == batch_id)
    if search:
        filters.append(or_(Transaction.transaction_id.contains(search, autoescape=True), Transaction.account_id.contains(search, autoescape=True)))
    if risk_level == "pendiente":
        filters.append(AnalysisResult.transaction_id.is_(None))
    elif risk_level:
        filters.append(AnalysisResult.risk_level == risk_level)
    total = session.scalar(select(func.count()).select_from(Transaction).outerjoin(AnalysisResult).where(*filters))
    items = session.scalars(select(Transaction).outerjoin(AnalysisResult).where(*filters).order_by(Transaction.id).offset((page - 1) * page_size).limit(page_size)).all()
    return TransactionPage(items=[TransactionOut.model_validate(t) for t in items], total=total, page=page, page_size=page_size)

@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: Annotated[int, PathParam(ge=1, le=9223372036854775807)], session: DB):
    item = session.get(Transaction, transaction_id)
    if item is None:
        raise HTTPException(404, "Transacción no encontrada.")
    return item
