import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from fastapi.testclient import TestClient
from src.api.routes import app

client = TestClient(app)

def test_routes():
    # 1. Test index page
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "MAS-Diffusion-Lab" in res_index.text
    print("[PASS] GET / (Static Index served)")

    # 2. Test system status
    res_status = client.get("/api/system/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "ollama" in data_status
    assert "mock" in data_status
    print("[PASS] GET /api/system/status")

    # 3. Test simulation init
    payload = {
        "topology": "BA_SCALE_FREE",
        "num_nodes": 20,
        "seed_message": "Kiểm thử thông điệp API khoa học",
        "fact_checker_ratio": 0.1,
        "fact_checker_placement": "HUB_DEGREE",
        "cloud_ratio": 0.0,
        "temperature": 0.7,
        "max_hops": 5,
        "seed": 42
    }
    res_init = client.post("/api/simulation/init", json=payload)
    assert res_init.status_code == 200
    data_init = res_init.json()
    assert data_init["total_nodes"] == 20
    assert "graph_data" in data_init
    print("[PASS] POST /api/simulation/init")

    # 4. Test simulation step
    res_step = client.post("/api/simulation/step")
    assert res_step.status_code == 200
    data_step = res_step.json()
    assert "hop_summary" in data_step
    print("[PASS] POST /api/simulation/step")

    # 5. Test export
    res_export = client.post("/api/simulation/export")
    assert res_export.status_code == 200
    data_export = res_export.json()
    assert "files" in data_export
    print("[PASS] POST /api/simulation/export")

    print("\nALL API ENDPOINTS PASSED VERIFICATION 100%!")

if __name__ == "__main__":
    test_routes()
