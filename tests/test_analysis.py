import sys
import os
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from src.api.routes import app, engine
from src.api.analysis import build_analysis_payload, build_report_prompt

client = TestClient(app)

def test_analysis_report_logic():
    # 1. Khởi tạo và chạy 1 hop để có dữ liệu
    init_payload = {
        "topology": "BA_SCALE_FREE",
        "num_nodes": 6,
        "seed_message": "Tổ chức Y tế khuyến cáo duy trì lối sống lành mạnh.",
        "fact_checker_ratio": 0.2,
        "fact_checker_placement": "HUB_DEGREE",
        "cloud_ratio": 0.0,
        "temperature": 0.7,
        "max_hops": 3,
        "seed": 42
    }
    r_init = client.post("/api/simulation/init", json=init_payload)
    assert r_init.status_code == 200
    r_step = client.post("/api/simulation/step")
    assert r_step.status_code == 200

    # 2. Kiểm tra build payload và prompt
    payload = build_analysis_payload(engine)
    assert payload["simulation_id"] == engine.simulation_id
    assert len(payload["hop_metrics"]) >= 1
    assert len(payload["per_hop"]) >= 1
    assert len(payload["traces"]) >= 1
    print(f"[PASS] build_analysis_payload: {len(payload['traces'])} traces, {len(payload['per_hop'])} hops")

    prompt_all = build_report_prompt(payload, hop=None, compact=False)
    assert "CẤU HÌNH THỰC NGHIỆM" in prompt_all
    assert "CHỈ SỐ VĨ MÔ THEO HOP" in prompt_all
    assert "YÊU CẦU BÁO CÁO" in prompt_all
    print("[PASS] build_report_prompt (all hops) generated successfully")

    prompt_hop1 = build_report_prompt(payload, hop=1, compact=True)
    assert "Hop 1" in prompt_hop1
    print("[PASS] build_report_prompt (hop 1) generated successfully")

    # 3. Test API endpoint GET /api/analysis/data
    r_data = client.get("/api/analysis/data")
    assert r_data.status_code == 200
    d = r_data.json()
    assert d["simulation_id"] == engine.simulation_id
    assert "overall" in d
    assert "persona_stats" in d["overall"]
    print("[PASS] GET /api/analysis/data returned complete JSON schema")

    print("\nALL ANALYSIS UNIT TESTS PASSED 100%!")

if __name__ == "__main__":
    test_analysis_report_logic()
