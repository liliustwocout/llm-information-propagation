import sys
import os
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from src.api.routes import app

client = TestClient(app)

def test_routes():
    # 1. Test index page
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "MAS-Diffusion-Lab" in res_index.text
    print("[PASS] GET / (Static Index served)")

    # 2. Test analysis page
    res_an = client.get("/analysis")
    assert res_an.status_code == 200
    assert "Phân tích & Đánh giá Thực nghiệm" in res_an.text
    print("[PASS] GET /analysis (Analysis Page served)")

    # 3. Test system status
    res_status = client.get("/api/system/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "ollama" in data_status
    assert "mock" in data_status
    print("[PASS] GET /api/system/status")

    # 4. Test simulation init
    payload = {
        "topology": "BA_SCALE_FREE",
        "num_nodes": 10,
        "seed_message": "Kiểm thử thông điệp API khoa học",
        "fact_checker_ratio": 0.1,
        "fact_checker_placement": "HUB_DEGREE",
        "cloud_ratio": 0.0,
        "temperature": 0.7,
        "max_hops": 3,
        "seed": 42
    }
    res_init = client.post("/api/simulation/init", json=payload)
    assert res_init.status_code == 200
    data_init = res_init.json()
    assert data_init["total_nodes"] == 10
    assert "graph_data" in data_init
    print("[PASS] POST /api/simulation/init")

    # 5. Test simulation step
    res_step = client.post("/api/simulation/step")
    assert res_step.status_code == 200
    data_step = res_step.json()
    assert "hop_summary" in data_step
    print("[PASS] POST /api/simulation/step")

    # 6. Test analysis data endpoint
    res_an_data = client.get("/api/analysis/data")
    assert res_an_data.status_code == 200
    an_data = res_an_data.json()
    assert "hop_metrics" in an_data
    assert "per_hop" in an_data
    assert len(an_data["per_hop"]) >= 1
    assert "traces" in an_data
    assert "overall" in an_data
    print(f"[PASS] GET /api/analysis/data (Hop 1 data: {len(an_data['traces'])} traces)")

    # 7. Test export
    res_export = client.post("/api/simulation/export")
    assert res_export.status_code == 200
    data_export = res_export.json()
    assert "files" in data_export
    print("[PASS] POST /api/simulation/export")

    print("\nALL API ENDPOINTS INCL. ANALYSIS PASSED VERIFICATION 100%!")

if __name__ == "__main__":
    test_routes()
