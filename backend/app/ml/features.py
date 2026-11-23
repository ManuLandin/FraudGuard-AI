"""Variables deterministas; no aprenden de inferencia ni usan etiquetas."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted

FEATURE_NAMES = ["log_amount", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or not {"amount_cents", "timestamp"}.issubset(frame.columns):
        raise ValueError("Se requieren filas con amount_cents y timestamp.")
    if frame["amount_cents"].map(lambda value: isinstance(value, (bool, np.bool_))).any():
        raise ValueError("amount_cents debe ser un entero positivo, no booleano.")
    try:
        amount = pd.to_numeric(frame["amount_cents"], errors="raise").to_numpy(dtype=float)
        dates = []
        for value in frame["timestamp"]:
            stamp = pd.Timestamp(value)
            if pd.isna(stamp) or stamp.tzinfo is None:
                raise ValueError()
            dates.append(stamp.tz_convert("UTC"))
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Montos o fechas inválidos; las fechas necesitan zona horaria.") from None
    if not np.isfinite(amount).all() or (amount <= 0).any() or (amount > 99999999999999).any() or (amount != np.floor(amount)).any():
        raise ValueError("amount_cents debe contener enteros positivos finitos dentro del límite CSV.")
    return pd.DataFrame({"amount_cents": amount, "timestamp": pd.DatetimeIndex(dates)})


class TransactionFeatures(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        validate_frame(X)
        self.n_features_in_ = 2
        return self

    def transform(self, X):
        check_is_fitted(self)
        frame = validate_frame(X)
        dates = frame["timestamp"].dt
        hour = dates.hour.to_numpy() + dates.minute.to_numpy() / 60 + dates.second.to_numpy() / 3600
        weekday = dates.day_of_week.to_numpy()
        return np.column_stack((np.log1p(frame["amount_cents"].to_numpy() / 100), np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24), np.sin(2*np.pi*weekday/7), np.cos(2*np.pi*weekday/7)))

    def get_feature_names_out(self, input_features=None):
        return np.asarray(FEATURE_NAMES, dtype=object)
