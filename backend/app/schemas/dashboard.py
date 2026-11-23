from pydantic import BaseModel

class CountBucket(BaseModel):
    name: str
    count: int

class DailyBucket(BaseModel):
    date: str
    count: int
    amount_cents: str

class DashboardSummary(BaseModel):
    total: int
    analyzed: int
    pending: int
    anomalies: int
    anomaly_percentage: float | None
    amount_cents: str
    distribution: list[CountBucket]
    daily: list[DailyBucket]
    amount_distribution: list[CountBucket]

class ModelStatus(BaseModel):
    ready: bool
    message: str | None = None
    created_at: str | None = None
    fit_rows: int | None = None
    calibration_rows: int | None = None

class TrainingResult(BaseModel):
    created_at: str
    fit_rows: int
    calibration_rows: int

class AnalysisResponse(BaseModel):
    analyzed: int
    model_created_at: str

class BatchOut(BaseModel):
    id: int
    filename: str
    row_count: int
    created_at: str
