from pathlib import Path
import pandas as pd
import pytest
from app.services.csv_import import parse_csv

ROOT = Path(__file__).resolve().parents[2]
def dataset(name):
    return pd.DataFrame(parse_csv((ROOT/"datasets"/name).read_bytes(),10000))

def test_evaluation_compares_baseline_without_leakage():
    from app.ml.evaluation import evaluate
    reference=dataset("ml_training_synthetic.csv")
    test=dataset("ml_inference_synthetic.csv")
    result=evaluate(reference,test)
    assert result["labeled_rows"] == 30
    assert result["positive_labels"] == 10
    for name in ("isolation_forest","amount_baseline"):
        metrics=result[name]
        assert sum(sum(row) for row in metrics["confusion_matrix"]) == 30
        assert 0 <= metrics["recall"] <= 1
        assert 0 <= metrics["average_precision"] <= 1
    with pytest.raises(ValueError): evaluate(reference,reference)

def test_unlabeled_evaluation_does_not_invent_metrics():
    from app.ml.evaluation import evaluate
    report=evaluate(dataset("ml_training_synthetic.csv"),dataset("ml_inference_synthetic.csv").drop(columns="label"))
    assert report["labeled_rows"] == 0
    assert report["isolation_forest"]["precision"] is None
    assert report["isolation_forest"]["confusion_matrix"] is None

def test_single_class_and_invalid_labels():
    from app.ml.evaluation import evaluate
    reference=dataset("ml_training_synthetic.csv")
    test=dataset("ml_inference_synthetic.csv").assign(label=0)
    report=evaluate(reference,test)
    assert report["isolation_forest"]["roc_auc"] is None
    assert report["isolation_forest"]["recall"] is None
    with pytest.raises(ValueError): evaluate(reference,test.assign(label=2))
