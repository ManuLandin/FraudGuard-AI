from pydantic import BaseModel, ConfigDict

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_id: int
    transaction_id: str
    amount_cents: int
    timestamp: str
    account_id: str | None
    label: int | None
    user_id: str | None = None
    is_anomaly: int | None = None
    transaction_type: str | None = None
    merchant_category: str | None = None
    location: str | None = None
    anomaly_score: float | None = None
    risk_level: str | None = None
    model_created_at: str | None = None

class UploadResult(BaseModel):
    batch_id: int
    filename: str
    row_count: int
    preview: list[TransactionOut]

class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
