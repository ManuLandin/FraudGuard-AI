"""Entrenamiento, calibración y persistencia separados de la inferencia."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import tempfile
import warnings
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.pipeline import Pipeline
from app.ml.features import TransactionFeatures, validate_frame


def versions():
    return {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__}


@dataclass
class AnomalyModel:
    pipeline: Pipeline
    calibration: np.ndarray
    fit_rows: int
    calibration_rows: int
    fit_end: str
    calibration_start: str
    seed: int
    library_versions: dict = field(default_factory=versions)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: int = 1


def train(frame: pd.DataFrame, seed: int = 42) -> AnomalyModel:
    """El 75% inicial ajusta el bosque; el tramo posterior calibra percentiles."""
    validated = validate_frame(frame).sort_values("timestamp", kind="stable").reset_index(drop=True)
    if len(validated) < 80:
        raise ValueError("Se requieren al menos 80 transacciones para ajuste y calibración.")
    boundary = validated.iloc[int(len(validated) * .75)]["timestamp"]
    fit = validated.loc[validated.timestamp < boundary]
    calibration = validated.loc[validated.timestamp >= boundary]
    if len(fit) < 40 or len(calibration) < 20:
        raise ValueError("La separación temporal requiere al menos 40 filas de ajuste y 20 de calibración, sin dividir fechas iguales.")
    pipeline = Pipeline([("features", TransactionFeatures()), ("isolation", IsolationForest(n_estimators=200, max_samples=min(256, len(fit)), contamination="auto", random_state=seed, n_jobs=1))])
    pipeline.fit(fit)
    reference = np.sort(-pipeline.score_samples(calibration))
    return AnomalyModel(pipeline, reference, len(fit), len(calibration), fit.timestamp.max().isoformat(), calibration.timestamp.min().isoformat(), seed)


def infer(model: AnomalyModel, frame: pd.DataFrame) -> pd.DataFrame:
    """Solo transforma y puntúa; no ajusta ni modifica modelo/referencia."""
    validated = validate_frame(frame)
    raw = -model.pipeline.score_samples(validated)
    reference = model.calibration
    left = np.searchsorted(reference, raw, side="left")
    right = np.searchsorted(reference, raw, side="right")
    score = 100 * (left + right) / (2 * len(reference))
    return pd.DataFrame({"raw_anomaly_score": raw, "anomaly_score": score, "risk_level": np.where(score >= 99, "alto", np.where(score >= 95, "medio", "bajo")), "is_anomaly": score >= 99}, index=frame.index)


def save_model(model: AnomalyModel, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as temp:
        temporary = Path(temp.name)
    try:
        joblib.dump(model, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_model(path: Path) -> AnomalyModel:
    """Solo artefactos locales de confianza: joblib puede ejecutar código al cargar."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            model = joblib.load(path)
    except InconsistentVersionWarning:
        raise ValueError("Versión incompatible de scikit-learn; usa el lock del entrenamiento.") from None
    if not isinstance(model, AnomalyModel) or model.schema_version != 1:
        raise ValueError("Esquema de artefacto ML inválido.")
    if model.library_versions != versions():
        raise ValueError("Las versiones del entorno difieren del entrenamiento; usa su lock.")
    reference = model.calibration
    if not isinstance(reference, np.ndarray) or reference.ndim != 1 or len(reference) < 20 or not np.isfinite(reference).all() or (np.diff(reference) < 0).any():
        raise ValueError("Referencia de calibración inválida.")
    return model
