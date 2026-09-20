import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import shutil
from src.core.network import NetworkBuilder, TopologyType
from src.core.agent import LLMAgent, AgentPersona, AgentState
from src.core.metrics import MetricsCalculator
from src.adapters.mock_adapter import MockLLMAdapter
from src.adapters.router import ModelRouter
from src.core.engine import SimulationEngine
from src.storage.telemetry import TelemetryManager

def test_network_generation():
    """Kiểm tra khởi tạo các đồ thị mạng phức hợp."""
    for topo in [TopologyType.ER_RANDOM, TopologyType.WS_SMALL_WORLD, TopologyType.BA_SCALE_FREE, TopologyType.SBM_COMMUNITY]:
        G = NetworkBuilder.generate_graph(topology=topo, num_nodes=20, seed=42)
        assert G.number_of_nodes() == 20
        assert G.number_of_edges() > 0

        metrics = NetworkBuilder.compute_topological_metrics(G)
        assert "average_degree" in metrics
        assert "average_clustering" in metrics
        assert "average_path_length" in metrics

        vis_data = NetworkBuilder.export_for_visualization(G)
        assert len(vis_data["nodes"]) == 20
        assert len(vis_data["edges"]) == G.number_of_edges()

def test_metrics_calculation():
    """Kiểm tra tính toán các chỉ số toán học."""
    # Cosine
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    sim = MetricsCalculator.cosine_similarity(v1, v2)
    assert abs(sim - 1.0) < 1e-5

    drift = MetricsCalculator.semantic_drift_distance(v1, v2)
    assert abs(drift - 0.0) < 1e-5

    # Penetration
    pen = MetricsCalculator.compute_penetration_rate(50, 25)
    assert pen == 50.0

    # Polarization
    beliefs_consensus = [0.8, 0.8, 0.8, 0.8]
    assert MetricsCalculator.compute_polarization_index(beliefs_consensus) == 0.0

    beliefs_polarized = [1.0, 1.0, -1.0, -1.0]
    assert MetricsCalculator.compute_polarization_index(beliefs_polarized) == 1.0

def test_agent_parsing():
    """Kiểm tra phân tích phản hồi LLM của tác tử."""
    agent = LLMAgent(agent_id=1, persona=AgentPersona.FACT_CHECKER)
    raw_json = '{"reasoning": "Nghi ngờ tin giả", "decision": "COUNTER", "updated_belief": -0.8, "outgoing_message": "Cảnh báo tin giả"}'
    res = agent.parse_llm_response(raw_json)
    assert res["decision"] == "COUNTER"
    assert res["updated_belief"] == -0.8
    assert res["outgoing_message"] == "Cảnh báo tin giả"

    agent.update_state(res["decision"], res["updated_belief"])
    assert agent.state == AgentState.INOCULATED_SKEPTIC
    assert agent.belief_score == -0.8

def test_simulation_engine_run():
    """Kiểm tra chạy mô phỏng tích hợp 2 bước."""
    router = ModelRouter()
    engine = SimulationEngine(router=router)

    init_res = engine.initialize_simulation(
        topology=TopologyType.BA_SCALE_FREE,
        num_nodes=15,
        seed_message="Thử nghiệm thông điệp khoa học kiểm chuẩn",
        max_hops=3,
        seed=42
    )
    assert init_res["total_nodes"] == 15
    assert len(engine.informed_nodes) == 1

    # Chạy hop 1
    loop = asyncio.new_event_loop()
    step1_res = loop.run_until_complete(engine.step())
    assert "hop_summary" in step1_res
    assert step1_res["hop_summary"]["hop"] == 1
    assert len(engine.informed_nodes) >= 1

    # Chạy hop 2
    step2_res = loop.run_until_complete(engine.step())
    assert "hop_summary" in step2_res

    # Kiểm tra lưu vết
    telemetry = TelemetryManager(output_dir="experiments_test")
    saved = telemetry.save_experiment_run(
        simulation_id=engine.simulation_id,
        config=engine.config,
        hop_metrics=engine.hop_metrics_history,
        all_traces=engine.all_traces
    )
    assert os.path.exists(saved["json_path"])
    assert os.path.exists(saved["metrics_csv"])
    assert os.path.exists(saved["traces_csv"])

    # Dọn dẹp thư mục test
    shutil.rmtree("experiments_test", ignore_errors=True)
    loop.close()

if __name__ == "__main__":
    test_network_generation()
    print("[PASS] test_network_generation")
    test_metrics_calculation()
    print("[PASS] test_metrics_calculation")
    test_agent_parsing()
    print("[PASS] test_agent_parsing")
    test_simulation_engine_run()
    print("[PASS] test_simulation_engine_run")
    print("\nALL UNIT TESTS PASSED SUCCESSFULLY 100%!")
