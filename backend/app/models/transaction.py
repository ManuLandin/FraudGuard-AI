from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    row_count: Mapped[int]
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.now(timezone.utc).isoformat())

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("batch_id", "transaction_id"), CheckConstraint("amount_cents > 0"), CheckConstraint("label IS NULL OR label IN (0, 1)"))
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), index=True)
    transaction_id: Mapped[str] = mapped_column(String(100), index=True)
    amount_cents: Mapped[int]
    timestamp: Mapped[str] = mapped_column(String(40), index=True)
    account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    label: Mapped[int | None] = mapped_column(nullable=True)

    context = relationship("TransactionContext", uselist=False, lazy="selectin")

    @property
    def user_id(self):
        return self.account_id

    @property
    def is_anomaly(self):
        """Etiqueta de referencia, nunca la predicción."""
        return self.label

    @property
    def transaction_type(self):
        return self.context.transaction_type if self.context else None

    @property
    def merchant_category(self):
        return self.context.merchant_category if self.context else None

    @property
    def location(self):
        return self.context.location if self.context else None

    analysis = relationship("AnalysisResult", uselist=False, lazy="selectin")

    @property
    def anomaly_score(self):
        return self.analysis.anomaly_score if self.analysis else None

    @property
    def risk_level(self):
        return self.analysis.risk_level if self.analysis else None

    @property
    def model_created_at(self):
        return self.analysis.model_created_at if self.analysis else None

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), primary_key=True)
    anomaly_score: Mapped[float] = mapped_column(Float)
    raw_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(10), index=True)
    model_created_at: Mapped[str]
    analyzed_at: Mapped[str] = mapped_column(default=lambda: datetime.now(timezone.utc).isoformat())


class TransactionContext(Base):
    __tablename__ = "transaction_contexts"
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), primary_key=True)
    transaction_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    merchant_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
