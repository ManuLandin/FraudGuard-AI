from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest


def normal_data(count=240):
    rng = np.random.default_rng(42)
    start = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    return pd.DataFrame({"amount_cents": rng.integers(9000, 11000, count), "timestamp": [(start + timedelta(days=i)).isoformat() for i in range(count)], "label": np.zeros(count)})


def test_atypical_amounts_rank_above_unseen_normal_data():
    from app.ml.model import train, infer
    model = train(normal_data())
    normal = normal_data(20).assign(amount_cents=10000)
    normal["timestamp"] = [(pd.Timestamp(stamp) + timedelta(days=365)).isoformat() for stamp in normal.timestamp]
    atypical = normal.assign(amount_cents=90000000)
    assert np.median(infer(model, atypical)["anomaly_score"]) > np.median(infer(model, normal)["anomaly_score"])
    assert infer(model, atypical)["is_anomaly"].any()
    assert infer(model, normal)["anomaly_score"].between(0, 100).all()


def test_roundtrip_and_reproducibility(tmp_path):
    from app.ml.model import train, infer, save_model, load_model
    frame = normal_data()
    a, b = train(frame), train(frame)
    expected = infer(a, frame)
    pd.testing.assert_frame_equal(expected, infer(b, frame))
    target = tmp_path / "model.joblib"
    save_model(a, target)
    pd.testing.assert_frame_equal(expected, infer(load_model(target), frame))


def test_labels_and_inference_batch_do_not_change_scores():
    from app.ml.model import train, infer
    frame = normal_data()
    a = train(frame)
    b = train(frame.assign(label=1))
    pd.testing.assert_frame_equal(infer(a, frame), infer(b, frame))
    point = frame.iloc[:1]
    assert infer(a, point)["anomaly_score"].iloc[0] == infer(a, pd.concat([point, frame.assign(amount_cents=90000000)]))["anomaly_score"].iloc[0]


def test_calibration_is_excluded_from_fitting():
    from app.ml.model import train
    frame = normal_data()
    changed = frame.copy()
    changed.loc[180:, "amount_cents"] = 90000000
    a, b = train(frame), train(changed)
    np.testing.assert_array_equal(a.pipeline.named_steps["isolation"].score_samples(a.pipeline.named_steps["features"].transform(frame)), b.pipeline.named_steps["isolation"].score_samples(b.pipeline.named_steps["features"].transform(frame)))
    assert a.fit_rows == 180 and a.calibration_rows == 60


@pytest.mark.parametrize("change", ["empty", "few", "nan", "negative", "date", "timezone", "column"])
def test_invalid_training_data(change):
    from app.ml.model import train
    frame = normal_data()
    if change == "empty": frame = frame.iloc[:0]
    if change == "few": frame = frame.iloc[:10]
    if change == "nan": frame.loc[0, "amount_cents"] = np.nan
    if change == "negative": frame.loc[0, "amount_cents"] = -1
    if change == "date": frame.loc[0, "timestamp"] = "bad"
    if change == "timezone": frame.loc[0, "timestamp"] = "2026-01-01T12:00:00"
    if change == "column": frame = frame.drop(columns="amount_cents")
    with pytest.raises(ValueError): train(frame)


def test_equal_timestamps_cannot_cross_split():
    from app.ml.model import train
    with pytest.raises(ValueError): train(normal_data().assign(timestamp="2026-01-01T00:00:00Z"))


def test_untrusted_or_invalid_artifact(tmp_path):
    import joblib
    from app.ml.model import load_model
    target = tmp_path / "invalid.joblib"
    joblib.dump({"wrong": "schema"}, target)
    with pytest.raises(ValueError): load_model(target)


def test_feature_timezone_equivalence_and_label_exclusion():
    from app.ml.features import TransactionFeatures
    a = pd.DataFrame({"amount_cents": [10000], "timestamp": ["2026-01-01T12:00:00Z"], "label": [0]})
    b = a.assign(timestamp="2026-01-01T06:00:00-06:00", label=1)
    features = TransactionFeatures().fit(a)
    np.testing.assert_array_equal(features.transform(a), features.transform(b))
    assert features.transform(a).shape == (1, 5)


def test_cli_training_and_inference(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path
    frame = normal_data()
    frame["transaction_id"] = [f"synthetic-{i}" for i in range(len(frame))]
    frame["amount"] = frame.amount_cents / 100
    source = tmp_path / "synthetic.csv"
    frame[["transaction_id", "amount", "timestamp", "label"]].assign(label=0).to_csv(source, index=False)
    model, output = tmp_path / "model.joblib", tmp_path / "results.json"
    command = [sys.executable, "-m", "app.ml"]
    cwd = Path(__file__).resolve().parents[1]
    subprocess.run(command + ["train", "--csv", str(source), "--model", str(model)], cwd=cwd, check=True, capture_output=True, timeout=120)
    subprocess.run(command + ["analyze", "--csv", str(source), "--model", str(model), "--output", str(output)], cwd=cwd, check=True, capture_output=True, timeout=120)
    result = json.loads(output.read_text(encoding="utf-8"))
    assert len(result["results"]) == len(frame)
    assert "no son fraudes confirmados" in result["notice"]


def test_tied_reference_uses_midrank_and_inference_does_not_refit():
    from app.ml.model import train, infer
    model = train(normal_data())
    frame = normal_data(1)
    raw = -model.pipeline.score_samples(frame)[0]
    model.calibration[:] = raw
    before = model.calibration.copy()
    result = infer(model, frame)
    assert result["anomaly_score"].iloc[0] == 50
    assert result["risk_level"].iloc[0] == "bajo"
    np.testing.assert_array_equal(before, model.calibration)
