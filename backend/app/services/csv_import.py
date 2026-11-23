import csv
import io
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException

REQUIRED = {"transaction_id", "amount", "timestamp"}
OPTIONAL = {"account_id", "label", "user_id", "is_anomaly", "transaction_type", "merchant_category", "location"}

def parse_csv(data: bytes, max_rows: int) -> list[dict]:
    try:
        text = data.decode("utf-8-sig")
        if not text.strip() or "\x00" in text:
            raise ValueError("El archivo está vacío o contiene caracteres nulos.")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        headers = next(reader)
        if len(headers) != len(set(headers)) or not REQUIRED.issubset(headers) or set(headers) - REQUIRED - OPTIONAL:
            raise ValueError("Columnas inválidas. Se requieren transaction_id, amount y timestamp.")
        rows, seen = [], set()
        for line, values in enumerate(reader, start=2):
            if len(rows) >= max_rows:
                raise ValueError("El archivo excede el límite de filas.")
            if len(values) != len(headers):
                raise ValueError(f"Fila {line}: número de campos incorrecto.")
            row = dict(zip(headers, (v.strip() for v in values)))
            identifier = row["transaction_id"]
            if "user_id" in row and "account_id" in row and row["user_id"] != row["account_id"]:
                raise ValueError(f"Fila {line}: user_id y account_id no coinciden.")
            if "is_anomaly" in row and "label" in row and row["is_anomaly"] != row["label"]:
                raise ValueError(f"Fila {line}: is_anomaly y label no coinciden.")
            account = row.get("user_id", row.get("account_id")) or None
            if "user_id" in row and account is None:
                raise ValueError(f"Fila {line}: user_id vacío.")
            metadata = {key: row[key] for key in ("transaction_type", "merchant_category", "location") if key in row}
            if "transaction_type" in metadata and metadata["transaction_type"] not in {"compra", "transferencia", "retiro", "pago"}:
                raise ValueError(f"Fila {line}: transaction_type inválido.")
            if any(not value or len(value) > 100 or any(ord(c) < 32 for c in value) for value in metadata.values()):
                raise ValueError(f"Fila {line}: metadatos vacíos, demasiado largos o inválidos.")
            if not identifier or len(identifier) > 100 or identifier in seen or (account and len(account) > 100):
                raise ValueError(f"Fila {line}: identificador vacío, demasiado largo o duplicado.")
            if any(ord(c) < 32 for c in identifier + (account or "")):
                raise ValueError(f"Fila {line}: identificador con caracteres de control.")
            if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", row["amount"]):
                raise ValueError(f"Fila {line}: monto inválido; usa un valor positivo y hasta dos decimales.")
            cents = int(Decimal(row["amount"]) * 100)
            if cents <= 0:
                raise ValueError(f"Fila {line}: el monto debe ser positivo.")
            try:
                stamp = datetime.fromisoformat(row["timestamp"])
                if stamp.tzinfo is None or "T" not in row["timestamp"]:
                    raise ValueError()
                stamp = stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except (ValueError, OverflowError):
                raise ValueError(f"Fila {line}: fecha ISO 8601 con zona horaria requerida.") from None
            label = row.get("is_anomaly", row.get("label", ""))
            if label not in ("", "0", "1"):
                raise ValueError(f"Fila {line}: label debe ser 0, 1 o vacío.")
            seen.add(identifier)
            rows.append(dict(transaction_id=identifier, amount_cents=cents, timestamp=stamp, account_id=account, label=int(label) if label else None, **metadata))
        if not rows:
            raise ValueError("El archivo no contiene transacciones.")
        return rows
    except (UnicodeDecodeError, csv.Error, ValueError, StopIteration, InvalidOperation) as exc:
        message = "Se requiere un archivo CSV UTF-8 válido." if isinstance(exc, (UnicodeDecodeError, csv.Error, StopIteration)) else str(exc)
        raise HTTPException(422, detail=message) from None
