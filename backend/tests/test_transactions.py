import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app

VALID = b"transaction_id,amount,timestamp,account_id,label\na1,12.34,2026-11-12T10:00:00-06:00,demo,0\na2,99.50,2026-11-12T17:00:00Z,demo,1\n"

@pytest.fixture
def settings(tmp_path):
    return Settings(database_url="sqlite:///" + (tmp_path / "test.db").as_posix(), max_upload_bytes=1024, _env_file=None)

@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c

def upload(client, data=VALID, name="demo.csv"):
    return client.post("/api/transactions/upload", files={"file": (name, data, "text/csv")})

def test_import_list_detail_and_persistence(client, settings):
    result = upload(client)
    assert result.status_code == 201
    batch = result.json()
    assert batch["row_count"] == 2
    assert batch["preview"][0]["amount_cents"] == 1234
    assert batch["preview"][0]["timestamp"] == "2026-11-12T16:00:00Z"
    with TestClient(create_app(settings)) as reopened:
        listing = reopened.get("/api/transactions", params={"batch_id": batch["batch_id"], "page_size": 1}).json()
        assert listing["total"] == 2
        assert len(listing["items"]) == 1
        item = reopened.get("/api/transactions/" + str(listing["items"][0]["id"])).json()
        assert item["transaction_id"] == "a1"
        assert reopened.get("/api/transactions", params={"search": "a2"}).json()["total"] == 1
        assert reopened.get("/api/transactions", params={"page": 2, "page_size": 1}).json()["items"][0]["transaction_id"] == "a2"

@pytest.mark.parametrize("data", [b"", b" \n", b"transaction_id,amount,timestamp\n", b"wrong,columns\na,b\n", b'transaction_id,amount,timestamp\n"unclosed,4,date', b"transaction_id,amount,timestamp\na,1,2026-11-12T00:00:00Z,extra\n", b"transaction_id,amount,amount,timestamp\na,1,2,date\n", b"\xff\xfe"])
def test_invalid_files_do_not_persist(client, data):
    assert upload(client, data).status_code == 422
    assert client.get("/api/transactions").json()["total"] == 0

@pytest.mark.parametrize("replacement", [b"NaN", b"-1", b"1.001", b"Infinity"])
def test_invalid_amount_rejects_entire_batch(client, replacement):
    assert upload(client, VALID.replace(b"99.50", replacement)).status_code == 422
    assert client.get("/api/transactions").json()["total"] == 0

def test_size_limit(client):
    assert upload(client, b"x" * 1025).status_code == 413
    assert upload(client, b"x" * 70000).status_code == 413
    assert client.get("/api/transactions").json()["total"] == 0

def test_extension_and_missing_file(client):
    assert upload(client, name="demo.txt").status_code == 415
    assert client.post("/api/transactions/upload").status_code == 422

def test_duplicate_identifier(client):
    assert upload(client, VALID.replace(b"a2", b"a1")).status_code == 422

def test_timestamp_requires_timezone(client):
    assert upload(client, VALID.replace(b"2026-11-12T17:00:00Z", b"2026-11-12T17:00:00")).status_code == 422

def test_not_found_and_pagination_validation(client):
    assert client.get("/api/transactions/999").status_code == 404
    assert client.get("/api/transactions", params={"page": 0}).status_code == 422
    assert client.get("/api/transactions", params={"page_size": 101}).status_code == 422

def test_row_limit(settings):
    settings.max_csv_rows = 1
    with TestClient(create_app(settings)) as c:
        assert upload(c).status_code == 422
        assert c.get("/api/transactions").json()["total"] == 0


def test_streamed_multipart_limit_without_content_length(client):
    def chunks():
        for _ in range(70):
            yield b"x" * 1024
    response = client.post("/api/transactions/upload", content=chunks(), headers={"Content-Type": "multipart/form-data; boundary=test"})
    assert response.status_code == 413

def test_utf8_bom_and_minimum_columns(client):
    data = b"\xef\xbb\xbftransaction_id,amount,timestamp\r\nminimal,1,2026-11-12T00:00:00Z\r\n"
    response = upload(client, data)
    assert response.status_code == 201
    assert response.json()["preview"][0]["account_id"] is None
    assert response.json()["preview"][0]["label"] is None

def test_literal_search_and_safe_filename(client):
    result = upload(client, name="../../demo.csv")
    assert result.json()["filename"] == "demo.csv"
    assert client.get("/api/transactions", params={"search": "%"}).json()["total"] == 0

def test_upload_preflight(client):
    response = client.options("/api/transactions/upload", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

def test_invalid_import_leaves_no_batch(client):
    from sqlalchemy import select, func
    from app.models.transaction import ImportBatch
    assert upload(client, VALID.replace(b"99.50", b"invalid")).status_code == 422
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ImportBatch)) == 0


def test_database_failure_has_safe_response(client):
    from sqlalchemy import text
    with client.app.state.session_factory() as session:
        session.execute(text("DROP TABLE transactions"))
        session.commit()
    response = client.get("/api/transactions")
    assert response.status_code == 503
    assert "SQL" not in response.text
