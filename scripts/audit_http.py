"""Prueba HTTP real aislada: no toca la base ni el modelo del usuario."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix="fraudguard-audit-") as temporary:
        directory=Path(temporary)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]
        base=f"http://127.0.0.1:{port}"
        env={**os.environ,"DATABASE_URL":"sqlite:///"+(directory/"test.db").as_posix(),"MODEL_PATH":str(directory/"model.joblib"),"MAX_UPLOAD_BYTES":"1024","MAX_CSV_ROWS":"10000"}
        # Referencia de 240 filas requiere más que 1 KiB; usar 5 MiB y probar el límite real.
        env["MAX_UPLOAD_BYTES"]="5242880"
        def request(path, data=None, headers=None, method=None):
            req=urllib.request.Request(base+path,data=data,headers={"Origin":"http://localhost:5173",**(headers or {})},method=method)
            try:
                with urllib.request.urlopen(req,timeout=60) as response:
                    return response.status,json.load(response),response.headers
            except urllib.error.HTTPError as response:
                return response.code,json.load(response),response.headers
        def start():
            process=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--app-dir",str(ROOT/"backend"),"--host","127.0.0.1","--port",str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            for _ in range(600):
                try:
                    if request("/health")[0]==200: return process
                except (OSError,ValueError): pass
                if process.poll() is not None: raise RuntimeError("Uvicorn terminó durante inicio.")
                time.sleep(.1)
            process.terminate();process.wait(timeout=15)
            raise TimeoutError("Uvicorn no inició.")
        def upload(data,name="synthetic.csv"):
            boundary="fraudguard-audit-boundary"
            body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: text/csv\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
            return request("/api/transactions/upload",body,{"Content-Type":f"multipart/form-data; boundary={boundary}"})
        def post(path,batch):
            return request(path,json.dumps({"batch_id":batch}).encode(),{"Content-Type":"application/json"})
        process=start()
        try:
            assert request("/health")[1]["status"]=="ok";checks.append("health")
            schema=request("/openapi.json")[1]
            for path,verb in [("/api/dashboard/summary","get"),("/api/ml/status","get"),("/api/ml/train","post"),("/api/ml/analyze","post")]:
                assert schema["paths"][path][verb]["responses"]["200"]["content"]["application/json"]["schema"]
            checks.append("openapi-response-contracts")
            for invalid in [b"",b"wrong,columns\nx,y\n",b'transaction_id,amount,timestamp\n"unclosed']:
                assert upload(invalid)[0]==422
            assert upload(b"x"*(5242881))[0]==413
            assert request("/api/transactions")[1]["total"]==0
            checks.append("empty-malformed-oversized-csv-no-persistence")
            training=upload((ROOT/"datasets/ml_training_synthetic.csv").read_bytes())
            assert training[0]==201
            evaluation=upload((ROOT/"datasets/ml_inference_synthetic.csv").read_bytes())
            assert evaluation[0]==201
            batch=evaluation[1]["batch_id"]
            assert post("/api/ml/train",training[1]["batch_id"])[0]==200
            assert post("/api/ml/analyze",batch)[1]["analyzed"]==30
            code,summary,headers=request(f"/api/dashboard/summary?batch_id={batch}")
            assert code==200 and summary["analyzed"]==30 and isinstance(summary["amount_cents"],str)
            assert headers["access-control-allow-origin"]=="http://localhost:5173"
            checks.append("upload-train-analyze-dashboard-cors")
            result=request(f"/api/transactions?batch_id={batch}&risk_level=alto")[1]
            assert result["total"]==summary["anomalies"]
            item=result["items"][0]
            assert request(f'/api/transactions/{item["id"]}')[1]["anomaly_score"]>=99
            assert len(request(f"/api/transactions?batch_id={batch}&page=2&page_size=10")[1]["items"])==10
            assert request("/api/transactions?page="+str(10**30))[0]==422
            checks.append("filters-pagination-detail-integer-bounds")
            process.terminate();process.wait(timeout=15)
            process=start()
            assert request(f"/api/dashboard/summary?batch_id={batch}")[1]==summary
            assert request("/api/ml/status")[1]["ready"]
            checks.append("persistence-after-real-process-restart")
        finally:
            process.terminate();process.wait(timeout=15)
    report={"passed":True,"checks":checks,"isolation":"temporary SQLite and model; real loopback HTTP"}
    target=ROOT/"docs/audit/http_checks.json";target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
