from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(database_url="sqlite:///"+(tmp_path/"db.sqlite").as_posix(), model_path=tmp_path/"model.joblib", _env_file=None))) as c:
        yield c

def upload(c, name):
    source=Path(__file__).resolve().parents[2]/"datasets"/name
    return c.post("/api/transactions/upload",files={"file":(name,source.read_bytes(),"text/csv")}).json()["batch_id"]

def test_full_dashboard_flow(client):
    assert client.get("/api/dashboard/summary").json()["total"] == 0
    assert not client.get("/api/ml/status").json()["ready"]
    batch=upload(client,"ml_inference_synthetic.csv")
    assert client.post("/api/ml/analyze",json={"batch_id":batch}).status_code == 409
    reference=upload(client,"ml_training_synthetic.csv")
    assert client.post("/api/ml/train",json={"batch_id":reference}).status_code == 200
    assert client.get("/api/ml/status").json()["ready"]
    assert client.post("/api/ml/analyze",json={"batch_id":batch}).json()["analyzed"] == 30
    summary=client.get("/api/dashboard/summary",params={"batch_id":batch}).json()
    assert summary["total"] == summary["analyzed"] == 30
    assert summary["anomalies"] > 0
    assert sum(x["count"] for x in summary["distribution"]) == 30
    assert sum(x["count"] for x in summary["daily"]) == 30
    assert sum(int(x["amount_cents"]) for x in summary["daily"]) == int(summary["amount_cents"])
    high=client.get("/api/transactions",params={"batch_id":batch,"risk_level":"alto","page_size":2}).json()
    assert high["total"] == summary["anomalies"]
    assert all(x["risk_level"] == "alto" and x["anomaly_score"]>=99 for x in high["items"])
    assert client.get("/api/transactions/"+str(high["items"][0]["id"])).json()["model_created_at"]
    assert client.post("/api/ml/analyze",json={"batch_id":batch}).json()["analyzed"] == 30
    assert client.get("/api/dashboard/summary",params={"batch_id":batch}).json()["analyzed"] == 30
    assert client.get("/api/transactions",params={"batch_id":reference,"risk_level":"pendiente"}).json()["total"] == 240
    assert len(client.get("/api/transactions/batches").json()) == 2

def test_invalid_ml_actions_and_filters(client):
    assert client.post("/api/ml/train",json={"batch_id":999}).status_code == 404
    assert client.post("/api/ml/analyze",json={"batch_id":999}).status_code == 404
    assert client.get("/api/transactions",params={"risk_level":"wrong"}).status_code == 422
    batch=upload(client,"example_synthetic.csv")
    assert client.post("/api/ml/train",json={"batch_id":batch}).status_code == 422
    assert not client.get("/api/ml/status").json()["ready"]


@pytest.mark.parametrize("path", ["/api/transactions?page="+str(10**30), "/api/transactions?batch_id="+str(10**30), "/api/transactions/"+str(10**30), "/api/dashboard/summary?batch_id="+str(10**30)])
def test_out_of_range_sqlite_integers_are_rejected(client,path):
    assert client.get(path).status_code == 422

@pytest.mark.parametrize("action",["train","analyze"])
def test_out_of_range_ml_batch(client,action):
    assert client.post("/api/ml/"+action,json={"batch_id":10**30}).status_code == 422


def test_large_monetary_totals_preserve_cents(client):
    data="transaction_id,amount,timestamp\n"+"".join(f"large-{i},999999999999.99,2027-01-01T12:00:00Z\n" for i in range(99))
    result=client.post("/api/transactions/upload",files={"file":("large.csv",data.encode(),"text/csv")})
    assert result.status_code == 201
    summary=client.get("/api/dashboard/summary").json()
    assert summary["amount_cents"] == "9899999999999901"
    assert summary["daily"][0]["amount_cents"] == "9899999999999901"
