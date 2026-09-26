"""
MAS-Diffusion-Lab: Script Thực Nghiệm Tự Động Hóa Hàng Loạt (Batch Experiment Runner)
Dành cho đề tài NCKH 2026:
"Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"

Chế độ chạy:
  - quick:  2 kịch bản đối chứng nhanh (BA, 0% vs 20% FC)
  - matrix: 7 kịch bản đại diện (4 Topo × tỷ lệ FC tiêu biểu)
  - full:   Ma trận đầy đủ 36 kịch bản × K seeds (dành cho bài báo NCKH)
"""

import sys
import os
import asyncio
import time
import csv
import argparse
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Đảm bảo đường dẫn module gốc
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.network import TopologyType
from src.core.engine import SimulationEngine
from src.adapters.router import ModelRouter
from src.storage.telemetry import TelemetryManager


# ═══════════════════════════════════════════════════════════════════
# Ma trận Kịch bản Thực nghiệm Đầy đủ (Factorial Design)
# ═══════════════════════════════════════════════════════════════════

# 4 loại Topo mạng chuẩn hóa
TOPOLOGIES = [
    TopologyType.BA_SCALE_FREE,
    TopologyType.WS_SMALL_WORLD,
    TopologyType.ER_RANDOM,
    TopologyType.SBM_COMMUNITY,
]

# 3 tỷ lệ can thiệp Fact-Checker
FC_RATIOS = [0.0, 0.10, 0.20]

# 3 chiến lược bố trí Fact-Checker
FC_PLACEMENTS = ["RANDOM", "HUB_DEGREE", "BRIDGE_BETWEENNESS"]

# Thông điệp hạt giống chuẩn hóa cho mọi phiên thực nghiệm
SEED_MESSAGE = (
    "Tổ chức Y tế khuyến nghị duy trì vận động thể chất "
    "30 phút mỗi ngày để giảm 40% nguy cơ tim mạch."
)


def build_full_matrix() -> List[Tuple[TopologyType, float, str]]:
    """
    Sinh ma trận giai thừa đầy đủ:
    4 Topologies × 3 FC Ratios × 3 Placements = 36 kịch bản.
    Lưu ý: Khi FC Ratio = 0.0, Placement không có ý nghĩa → chỉ giữ 1 lần.
    """
    scenarios = []
    for topo in TOPOLOGIES:
        for fc_ratio in FC_RATIOS:
            if fc_ratio == 0.0:
                # Không có Fact-Checker → Placement không ảnh hưởng, chỉ chạy 1 lần
                scenarios.append((topo, fc_ratio, "NONE"))
            else:
                for placement in FC_PLACEMENTS:
                    scenarios.append((topo, fc_ratio, placement))
    return scenarios


def build_matrix_scenarios() -> List[Tuple[TopologyType, float, str]]:
    """7 kịch bản đại diện (tương thích ngược với mode matrix cũ)."""
    return [
        (TopologyType.BA_SCALE_FREE, 0.0, "NONE"),
        (TopologyType.BA_SCALE_FREE, 0.1, "HUB_DEGREE"),
        (TopologyType.BA_SCALE_FREE, 0.2, "HUB_DEGREE"),
        (TopologyType.WS_SMALL_WORLD, 0.0, "NONE"),
        (TopologyType.WS_SMALL_WORLD, 0.1, "HUB_DEGREE"),
        (TopologyType.ER_RANDOM, 0.0, "NONE"),
        (TopologyType.SBM_COMMUNITY, 0.1, "BRIDGE_BETWEENNESS"),
    ]


def build_quick_scenarios() -> List[Tuple[TopologyType, float, str]]:
    """2 kịch bản đối chứng nhanh."""
    return [
        (TopologyType.BA_SCALE_FREE, 0.0, "NONE"),
        (TopologyType.BA_SCALE_FREE, 0.2, "HUB_DEGREE"),
    ]


# ═══════════════════════════════════════════════════════════════════
# Hàm Thực thi Thực nghiệm Đơn lẻ
# ═══════════════════════════════════════════════════════════════════

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
    seed_message: str,
    scenario_idx: int = 0,
    total_scenarios: int = 1,
) -> Dict[str, Any]:
    """Thực thi một đợt mô phỏng độc lập qua toàn bộ các Hop."""
    placement_label = fact_checker_placement if fact_checker_ratio > 0 else "N/A"
    print(f"\n{'='*70}")
    print(
        f"[{scenario_idx}/{total_scenarios}] "
        f"Topo={topology.value} | FC={fact_checker_ratio*100:.0f}% | "
        f"Placement={placement_label} | Seed={seed} | Model={local_model}"
    )
    print(f"{'='*70}")

    # Khi FC = 0, đặt placement = RANDOM (không ảnh hưởng vì count = 0)
    actual_placement = fact_checker_placement if fact_checker_ratio > 0 else "RANDOM"

    init_res = engine.initialize_simulation(
        topology=topology,
        num_nodes=num_nodes,
        seed_message=seed_message,
        local_model=local_model,
        fact_checker_ratio=fact_checker_ratio,
        fact_checker_placement=actual_placement,
        cloud_ratio=0.0,
        temperature=0.7,
        max_hops=max_hops,
        seed=seed,
    )

    t_start = time.time()
    final_hop = 0

    for hop in range(1, max_hops + 1):
        step_res = await engine.step()
        summary = step_res.get("hop_summary", {})
        if not summary:
            print(f"  [-] Hop {hop}: Không còn thông điệp lan truyền.")
            break

        final_hop = summary.get("hop", hop)
        print(
            f"  → Hop {final_hop}: "
            f"R(t)={summary.get('penetration_rate')}% | "
            f"Drift={summary.get('average_semantic_drift')} | "
            f"PI={summary.get('polarization_index')} | "
            f"R_t={summary.get('reproduction_rate')} | "
            f"Queue={summary.get('remaining_queue_size')}"
        )

        if step_res.get("finished"):
            break

    total_time = round(time.time() - t_start, 2)
    print(f"  [✓] Hoàn thành sau {total_time}s ({final_hop} hops).")

    # Lưu vết Telemetry chuẩn NCKH
    saved = telemetry.save_experiment_run(
        simulation_id=engine.simulation_id,
        config=engine.config,
        hop_metrics=engine.hop_metrics_history,
        all_traces=engine.all_traces,
    )
    print(f"  [+] CSV: {saved['metrics_csv']}")

    # Trích xuất chỉ số cuối cùng
    last_metrics = engine.hop_metrics_history[-1] if engine.hop_metrics_history else {}
    return {
        "simulation_id": engine.simulation_id,
        "topology": topology.value,
        "fc_ratio": fact_checker_ratio,
        "fc_placement": fact_checker_placement,
        "seed": seed,
        "model": local_model,
        "num_nodes": num_nodes,
        "max_hops_config": max_hops,
        "actual_hops": final_hop,
        "time_seconds": total_time,
        "final_coverage_pct": last_metrics.get("penetration_rate", 0.0),
        "final_drift": last_metrics.get("average_semantic_drift", 0.0),
        "final_polarization": last_metrics.get("polarization_index", 0.0),
        "final_R_t": last_metrics.get("reproduction_rate", 0.0),
        "final_informed_total": last_metrics.get("informed_total", 0),
        "csv_path": saved["metrics_csv"],
    }


# ═══════════════════════════════════════════════════════════════════
# Xuất File Tổng hợp CSV (Aggregated Summary)
# ═══════════════════════════════════════════════════════════════════

def save_aggregated_summary(results: List[Dict[str, Any]], output_dir: str) -> str:
    """
    Ghi toàn bộ kết quả tổng hợp ra 1 file CSV duy nhất,
    phục vụ nhập vào script phân tích ANOVA / Pandas.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(output_dir, f"SUMMARY_{timestamp_str}.csv")

    fieldnames = [
        "simulation_id", "topology", "fc_ratio", "fc_placement", "seed",
        "model", "num_nodes", "max_hops_config", "actual_hops", "time_seconds",
        "final_coverage_pct", "final_drift", "final_polarization", "final_R_t",
        "final_informed_total",
    ]

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return summary_path


# ═══════════════════════════════════════════════════════════════════
# Bảng Tổng kết In ra Màn hình
# ═══════════════════════════════════════════════════════════════════

def print_summary_table(results: List[Dict[str, Any]]):
    """In bảng tổng kết kết quả thực nghiệm ra console."""
    header = (
        f"{'#':<4} {'Topology':<16} {'FC%':<6} {'Placement':<20} "
        f"{'Seed':<6} {'R(t)%':<8} {'Drift':<8} {'PI':<8} "
        f"{'R_t':<6} {'Hops':<5} {'Time':<8}"
    )
    print(f"\n{'═'*100}")
    print("BẢNG TỔNG KẾT DỮ LIỆU THỰC NGHIỆM")
    print(f"{'═'*100}")
    print(header)
    print(f"{'─'*100}")

    for i, r in enumerate(results, 1):
        placement = r["fc_placement"] if r["fc_ratio"] > 0 else "N/A"
        print(
            f"{i:<4} {r['topology']:<16} {r['fc_ratio']*100:<5.0f}% "
            f"{placement:<20} {r['seed']:<6} "
            f"{r['final_coverage_pct']:<7.1f}% {r['final_drift']:<8.4f} "
            f"{r['final_polarization']:<8.4f} {r['final_R_t']:<6.2f} "
            f"{r['actual_hops']:<5} {r['time_seconds']}s"
        )

    print(f"{'═'*100}")
    print(f"Tổng số phiên thực nghiệm: {len(results)}")


# ═══════════════════════════════════════════════════════════════════
# Hàm Chính (Main Entry Point)
# ═══════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="MAS-Diffusion-Lab: Chạy thực nghiệm ma trận lan truyền thông tin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Chạy nhanh 2 kịch bản đối chứng:
  python run_experiments.py --mode quick --model qwen2.5:3b

  # Chạy 7 kịch bản đại diện:
  python run_experiments.py --mode matrix --model qwen2.5:3b --nodes 15 --hops 4

  # Chạy ma trận đầy đủ cho bài báo NCKH (28 kịch bản × 10 seeds = 280 phiên):
  python run_experiments.py --mode full --model qwen2.5:3b --nodes 15 --hops 4 --seeds 42 43 44 45 46 47 48 49 50 51

  # Chạy ma trận đầy đủ với 3 seeds (để test nhanh):
  python run_experiments.py --mode full --model qwen2.5:3b --nodes 15 --hops 4 --seeds 42 43 44
        """,
    )
    parser.add_argument(
        "--model", type=str, default="qwen2.5:3b",
        help="Mô hình Ollama: qwen2.5:3b, llama3:8b (mặc định: qwen2.5:3b)",
    )
    parser.add_argument(
        "--nodes", type=int, default=15,
        help="Số lượng tác tử trong mạng (mặc định: 15)",
    )
    parser.add_argument(
        "--hops", type=int, default=4,
        help="Số hop tối đa (mặc định: 4)",
    )
    parser.add_argument(
        "--mode", type=str, default="quick",
        choices=["quick", "matrix", "full"],
        help="quick: 2 đợt; matrix: 7 đợt đại diện; full: ma trận 28 kịch bản × K seeds",
    )
    parser.add_argument(
        "--seeds", type=int, nargs="+", default=[42],
        help="Danh sách seeds ngẫu nhiên (mặc định: [42]). VD: --seeds 42 43 44 45 46 47 48 49 50 51",
    )
    parser.add_argument(
        "--output-dir", type=str, default="experiments",
        help="Thư mục lưu kết quả (mặc định: experiments)",
    )
    args = parser.parse_args()

    # Kiểm tra trạng thái hệ thống mô hình
    router = ModelRouter()
    providers = await router.check_all_providers()
    print("╔══════════════════════════════════════════════════════╗")
    print("║      MAS-Diffusion-Lab — Batch Experiment Runner    ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Ollama Online : {str(providers['ollama']['online']):<36}║")
    print(f"║  Models Ready  : {str(providers['ollama'].get('available_models', [])):<36}║")
    print(f"║  Selected Model: {args.model:<36}║")
    print(f"║  Mode          : {args.mode:<36}║")
    print(f"║  Nodes         : {args.nodes:<36}║")
    print(f"║  Max Hops      : {args.hops:<36}║")
    print(f"║  Seeds         : {str(args.seeds):<36}║")
    print("╚══════════════════════════════════════════════════════╝\n")

    engine = SimulationEngine(router=router)
    telemetry = TelemetryManager(output_dir=args.output_dir)

    # Chọn tập kịch bản theo mode
    if args.mode == "quick":
        scenarios = build_quick_scenarios()
    elif args.mode == "matrix":
        scenarios = build_matrix_scenarios()
    else:  # full
        scenarios = build_full_matrix()

    # Tính tổng số phiên thực nghiệm
    total_runs = len(scenarios) * len(args.seeds)
    print(f"📋 Tổng số phiên thực nghiệm: {len(scenarios)} kịch bản × {len(args.seeds)} seeds = {total_runs} phiên\n")

    all_start = time.time()
    results: List[Dict[str, Any]] = []
    run_counter = 0

    for seed in args.seeds:
        for topo, fc_ratio, placement in scenarios:
            run_counter += 1
            try:
                res = await run_single_experiment(
                    engine=engine,
                    telemetry=telemetry,
                    topology=topo,
                    num_nodes=args.nodes,
                    fact_checker_ratio=fc_ratio,
                    fact_checker_placement=placement,
                    local_model=args.model,
                    max_hops=args.hops,
                    seed=seed,
                    seed_message=SEED_MESSAGE,
                    scenario_idx=run_counter,
                    total_scenarios=total_runs,
                )
                results.append(res)
            except Exception as e:
                print(f"  [✗] LỖI: {e}")
                results.append({
                    "simulation_id": "ERROR",
                    "topology": topo.value,
                    "fc_ratio": fc_ratio,
                    "fc_placement": placement,
                    "seed": seed,
                    "model": args.model,
                    "num_nodes": args.nodes,
                    "max_hops_config": args.hops,
                    "actual_hops": 0,
                    "time_seconds": 0,
                    "final_coverage_pct": 0.0,
                    "final_drift": 0.0,
                    "final_polarization": 0.0,
                    "final_R_t": 0.0,
                    "final_informed_total": 0,
                    "csv_path": "",
                })

    total_elapsed = round(time.time() - all_start, 2)

    # In bảng tổng kết
    print_summary_table(results)

    # Xuất file tổng hợp CSV
    summary_path = save_aggregated_summary(results, args.output_dir)
    print(f"\n📊 File tổng hợp CSV (cho phân tích ANOVA): {summary_path}")
    print(f"⏱  Tổng thời gian chạy: {total_elapsed}s ({total_elapsed/60:.1f} phút)")
    print(f"📁 Toàn bộ dữ liệu chi tiết đã lưu trong: {args.output_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
