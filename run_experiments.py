"""
MAS-Diffusion-Lab: Script Thực Nghiệm Tự Động Hóa Hàng Loạt (Batch Experiment Runner)
Dành cho đề tài NCKH 2026:
"Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"
"""

import sys
import os
import asyncio
import time
import argparse
from typing import List, Dict, Any

# Đảm bảo đường dẫn module gốc
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.network import TopologyType
from src.core.engine import SimulationEngine
from src.adapters.router import ModelRouter
from src.storage.telemetry import TelemetryManager

async def run_single_experiment(
    engine: SimulationEngine,
    telemetry: TelemetryManager,
    topology: TopologyType,
    num_nodes: int,
    fact_checker_ratio: float,
    fact_checker_placement: str,
    local_model: str,
    max_hops: int,
    seed: int,
    seed_message: str
) -> Dict[str, Any]:
    """Thực thi một đợt mô phỏng độc lập qua toàn bộ các Hop."""
    print(f"\n========================================================")
    print(f"[*] Bắt đầu thực nghiệm: Topo={topology.value} | N={num_nodes} | FC_Ratio={fact_checker_ratio*100}% | Model={local_model}")
    print(f"========================================================")

    init_res = engine.initialize_simulation(
        topology=topology,
        num_nodes=num_nodes,
        seed_message=seed_message,
        local_model=local_model,
        fact_checker_ratio=fact_checker_ratio,
        fact_checker_placement=fact_checker_placement,
        cloud_ratio=0.0,
        temperature=0.7,
        max_hops=max_hops,
        seed=seed
    )

    t_start = time.time()

    for hop in range(1, max_hops + 1):
        step_res = await engine.step()
        summary = step_res.get("hop_summary", {})
        if not summary:
            print(f"[-] Hop {hop}: Đã hoàn tất hoặc không còn thông điệp lan truyền.")
            break

        print(
            f"  -> Hop {summary.get('hop')}: "
            f"Độ phủ R(t) = {summary.get('penetration_rate')}% | "
            f"Drift = {summary.get('average_semantic_drift')} | "
            f"Phân cực PI = {summary.get('polarization_index')} | "
            f"Hàng đợi = {summary.get('remaining_queue_size')} tin"
        )

        if step_res.get("finished"):
            break

    total_time = round(time.time() - t_start, 2)
    print(f"[✓] Hoàn thành thực nghiệm sau {total_time}s.")

    # Lưu vết Telemetry chuẩn NCKH
    saved = telemetry.save_experiment_run(
        simulation_id=engine.simulation_id,
        config=engine.config,
        hop_metrics=engine.hop_metrics_history,
        all_traces=engine.all_traces
    )
    print(f"[+] Dữ liệu đã lưu: {saved['metrics_csv']}")
    return {
        "simulation_id": engine.simulation_id,
        "topology": topology.value,
        "fc_ratio": fact_checker_ratio,
        "time_s": total_time,
        "final_coverage": engine.hop_metrics_history[-1].get("penetration_rate", 0.0) if engine.hop_metrics_history else 0.0,
        "final_drift": engine.hop_metrics_history[-1].get("average_semantic_drift", 0.0) if engine.hop_metrics_history else 0.0,
        "csv": saved["metrics_csv"]
    }

async def main():
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm ma trận lan truyền thông tin MAS-Diffusion-Lab")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Mô hình Ollama: qwen2.5:3b, llama3:8b")
    parser.add_argument("--nodes", type=int, default=15, help="Số lượng tác tử (mặc định: 15)")
    parser.add_argument("--hops", type=int, default=4, help="Số hop tối đa (mặc định: 4)")
    parser.add_argument("--mode", type=str, default="quick", choices=["quick", "matrix"], help="quick: 2 đợt; matrix: đầy đủ 4 topologies")
    args = parser.parse_args()

    router = ModelRouter()
    providers = await router.check_all_providers()
    print("=== TRẠNG THÁI HỆ THỐNG MÔ HÌNH ===")
    print(f"Ollama Online: {providers['ollama']['online']}")
    print(f"Mô hình sẵn sàng: {providers['ollama'].get('available_models', [])}")
    print(f"Mô hình lựa chọn: {args.model}")
    print("===================================\n")

    engine = SimulationEngine(router=router)
    telemetry = TelemetryManager(output_dir="experiments")

    seed_message = "Tổ chức Y tế khuyến nghị duy trì vận động thể chất 30 phút mỗi ngày để giảm 40% nguy cơ tim mạch."

    if args.mode == "quick":
        scenarios = [
            (TopologyType.BA_SCALE_FREE, 0.0, "HUB_DEGREE"),
            (TopologyType.BA_SCALE_FREE, 0.2, "HUB_DEGREE"),
        ]
    else:
        scenarios = [
            (TopologyType.BA_SCALE_FREE, 0.0, "HUB_DEGREE"),
            (TopologyType.BA_SCALE_FREE, 0.1, "HUB_DEGREE"),
            (TopologyType.BA_SCALE_FREE, 0.2, "HUB_DEGREE"),
            (TopologyType.WS_SMALL_WORLD, 0.0, "HUB_DEGREE"),
            (TopologyType.WS_SMALL_WORLD, 0.1, "HUB_DEGREE"),
            (TopologyType.ER_RANDOM, 0.0, "RANDOM"),
            (TopologyType.SBM_COMMUNITY, 0.1, "BRIDGE_BETWEENNESS"),
        ]

    results = []
    for topo, fc_ratio, placement in scenarios:
        res = await run_single_experiment(
            engine=engine,
            telemetry=telemetry,
            topology=topo,
            num_nodes=args.nodes,
            fact_checker_ratio=fc_ratio,
            fact_checker_placement=placement,
            local_model=args.model,
            max_hops=args.hops,
            seed=42,
            seed_message=seed_message
        )
        results.append(res)

    print("\n================ TỔNG KẾT BẢNG DỮ LIỆU THỰC NGHIỆM ================")
    print(f"{'Topology':<16} | {'FC Ratio':<8} | {'Độ phủ R(t)':<12} | {'Drift':<8} | {'Thời gian':<10}")
    print("-" * 65)
    for r in results:
        print(f"{r['topology']:<16} | {r['fc_ratio']*100:<7.0f}% | {r['final_coverage']:<11.1f}% | {r['final_drift']:<8.3f} | {r['time_s']}s")
    print("====================================================================")
    print("Toàn bộ tệp CSV / JSON đã được lưu trữ an toàn trong thư mục 'experiments/'.")

if __name__ == "__main__":
    asyncio.run(main())
