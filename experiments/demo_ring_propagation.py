"""
MAS-Diffusion-Lab: Kịch bản Thử nghiệm Truyền tin Mạng Vòng (Ring Topology 3-5 Tác tử)
ĐỀ TÀI NCKH 2026 - NHÓM 1
- Đề tài: "Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình
          lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"
- Chủ nhiệm đề tài: Nguyễn Văn An (MSSV: 23010163)
- Thành viên: Lê Phạm Thành Đạt (MSSV: 23010541)
- Giảng viên hướng dẫn: TS. Phạm Ngọc Hưng (Trường CNTT Phenikaa)
- Mục tiêu: Sản phẩm nghiệm thu Giai đoạn đầu (14 ngày) theo Hướng dẫn Lộ trình NCKH.
"""

import sys
import os
import asyncio
import time
import argparse
import json
import csv
from typing import List, Dict, Any

# Đảm bảo import được các module từ thư mục gốc src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import networkx as nx
import matplotlib
matplotlib.use("Agg") # Đảm bảo chạy tốt trên headless server/script
import matplotlib.pyplot as plt

from src.core.network import NetworkBuilder, TopologyType
from src.core.agent import LLMAgent, AgentPersona, AgentState
from src.core.metrics import MetricsCalculator
from src.adapters.router import ModelRouter

async def run_ring_propagation(
    num_nodes: int = 5,
    model_type: str = "OLLAMA",
    model_name: str = "llama3:8b",
    seed_message: str = "Tổ chức Y tế Thế giới (WHO) khuyến cáo tiêm chủng đầy đủ để phòng ngừa các biến thể cúm mùa trong năm 2026.",
    output_dir: str = "experiments"
):
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*70)
    print("[*] DAI HOC PHENIKAA - TRUONG CONG NGHE THONG TIN")
    print("[*] BÁO CÁO THỰC NGHIỆM TRUYỀN TIN TRÊN MẠNG VÒNG (14 NGÀY ĐẦU)")
    print("="*70)
    print(f"[*] Cấu hình thực nghiệm:")
    print(f"  - Cấu trúc mạng: Mạng vòng (Ring Topology, N = {num_nodes} tác tử)")
    print(f"  - Mô hình AI: {model_type} ({model_name})")
    print(f"  - Thông điệp hạt giống ban đầu (M0): \"{seed_message}\"")
    print("="*70 + "\n")

    # 1. Khởi tạo đồ thị mạng vòng (Cycle Graph)
    G = NetworkBuilder.generate_graph(topology=TopologyType.RING, num_nodes=num_nodes)
    router = ModelRouter()

    # 2. Khởi tạo các tác tử
    # Để kiểm tra chân thực hiện tượng truyền tin và phản biện:
    # Gán tác tử 0: Người phát tán ban đầu
    # Gán tác tử 1..N-2: Người dùng mạng xã hội (Gullible / Partisan / Leader)
    # Gán tác tử cuối cùng: Fact-Checker kiểm chứng
    personas = [
        AgentPersona.OPINION_LEADER,
        AgentPersona.GULLIBLE_SPREADER,
        AgentPersona.DOGMATIC_PARTISAN,
        AgentPersona.NEUTRAL_OBSERVER,
        AgentPersona.FACT_CHECKER
    ]
    
    agents: Dict[int, LLMAgent] = {}
    for i in range(num_nodes):
        persona = personas[i % len(personas)]
        agent = LLMAgent(
            agent_id=i,
            persona=persona,
            model_type=model_type,
            model_name=model_name,
            initial_belief=0.5 if i == 0 else 0.0
        )
        agents[i] = agent

    # 3. Vector embedding của thông điệp gốc M0
    v_origin = await router.embed_text(seed_message)

    # 4. Vòng lặp truyền tin tuần tự vòng tròn: 0 -> 1 -> 2 -> ... -> N-1
    conversation_logs: List[Dict[str, Any]] = []
    hop_metrics: List[Dict[str, Any]] = []

    current_msg = seed_message
    
    # Ghi nhận trạng thái ban đầu Hop 0
    hop_metrics.append({
        "hop": 0,
        "sender_id": "ORIGIN",
        "receiver_id": 0,
        "persona": agents[0].persona.value,
        "cosine_sim_origin": 1.0,
        "semantic_drift": 0.0,
        "bert_score_f1": 1.0,
        "nli_label": "ENTAILMENT",
        "hallucination_rate": 0.0,
        "message": seed_message
    })

    for hop in range(1, num_nodes):
        sender_id = hop - 1
        receiver_id = hop
        agent = agents[receiver_id]

        print(f"[*] Đang thực thi Bước nhảy (Hop) #{hop}: Tác tử #{sender_id} -> Tác tử #{receiver_id} ({agent.persona.value})...")
        t0 = time.time()

        prompt = agent.build_decision_prompt(
            incoming_message=current_msg,
            sender_id=sender_id,
            hop_count=hop
        )

        raw_output = await router.generate_for_agent(
            model_type=agent.model_type,
            model_name=agent.model_name,
            prompt=prompt,
            temperature=0.7,
            seed=42 + hop
        )
        latency = round(time.time() - t0, 2)

        parsed = agent.parse_llm_response(raw_output)
        agent.update_state(parsed["decision"], parsed["updated_belief"])

        outgoing_msg = parsed["outgoing_message"] if parsed["outgoing_message"] else current_msg

        # Tính toán các chỉ số Hybrid Metrics
        v_current = await router.embed_text(outgoing_msg)
        cos_sim = round(MetricsCalculator.cosine_similarity(v_origin, v_current), 4)
        drift = MetricsCalculator.semantic_drift_distance(v_origin, v_current)
        bert_res = MetricsCalculator.compute_bert_score(reference=seed_message, candidate=outgoing_msg)
        nli_res = MetricsCalculator.compute_nli_entailment(premise=seed_message, hypothesis=outgoing_msg)
        halu_res = MetricsCalculator.compute_hallucination_rate(source_text=seed_message, generated_text=outgoing_msg)

        step_data = {
            "hop": hop,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "persona": agent.persona.value,
            "decision": parsed["decision"],
            "reasoning": parsed["reasoning"],
            "belief_score": parsed["updated_belief"],
            "cosine_sim_origin": cos_sim,
            "semantic_drift": drift,
            "bert_score_f1": bert_res["f1"],
            "nli_label": nli_res["label"],
            "nli_entailment": nli_res["entailment"],
            "hallucination_rate": halu_res["hallucination_rate"],
            "latency_s": latency,
            "incoming_message": current_msg,
            "outgoing_message": outgoing_msg
        }

        conversation_logs.append(step_data)
        hop_metrics.append({
            "hop": hop,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "persona": agent.persona.value,
            "cosine_sim_origin": cos_sim,
            "semantic_drift": drift,
            "bert_score_f1": bert_res["f1"],
            "nli_label": nli_res["label"],
            "hallucination_rate": halu_res["hallucination_rate"],
            "message": outgoing_msg
        })

        print(f"  -> Quyết định: {parsed['decision']} | Độ tương đồng Cosine: {cos_sim} | F1-BERTScore: {bert_res['f1']} | NLI: {nli_res['label']} ({latency}s)")
        print(f"  -> Nội dung phát đi: \"{outgoing_msg[:90]}...\"\n")

        # Cập nhật thông điệp cho bước nhảy kế tiếp trong vòng
        current_msg = outgoing_msg

    # 5. Lưu tệp log hội thoại chi tiết (.txt)
    txt_log_path = os.path.join(output_dir, "ring_propagation_log.txt")
    with open(txt_log_path, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("NHẬT KÝ THỰC NGHIỆM TRUYỀN TIN MẠNG VÒNG (RING TOPOLOGY) - NCKH 2026 NHÓM 1\n")
        f.write("Sinh viên thực hiện: Nguyễn Văn An & Lê Phạm Thành Đạt\n")
        f.write("Giảng viên hướng dẫn: TS. Phạm Ngọc Hưng\n")
        f.write(f"Thời gian thực nghiệm: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Thông điệp gốc: {seed_message}\n")
        f.write("="*80 + "\n\n")

        for log in conversation_logs:
            f.write(f"--- BƯỚC NHẢY #{log['hop']}: Tác tử #{log['sender_id']} -> Tác tử #{log['receiver_id']} ({log['persona']}) ---\n")
            f.write(f"Thời gian suy luận: {log['latency_s']}s\n")
            f.write(f"Suy nghĩ (Reasoning): {log['reasoning']}\n")
            f.write(f"Quyết định (Decision): {log['decision']} | Điểm niềm tin: {log['belief_score']}\n")
            f.write(f"Chỉ số 1 (Cosine Similarity vs M0): {log['cosine_sim_origin']}\n")
            f.write(f"Chỉ số 2 (BERTScore F1 vs M0): {log['bert_score_f1']}\n")
            f.write(f"Chỉ số 3 (NLI Logic Status): {log['nli_label']} (Entailment Ratio: {log['nli_entailment']})\n")
            f.write(f"Chỉ số 4 (Tỷ lệ Ảo giác HaluEval): {log['hallucination_rate']}%\n")
            f.write(f"Nội dung nhận được: \"{log['incoming_message']}\"\n")
            f.write(f"Nội dung truyền tiếp: \"{log['outgoing_message']}\"\n\n")

    # 6. Lưu bảng số liệu đo lường (.csv)
    csv_path = os.path.join(output_dir, "ring_propagation_metrics.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hop", "sender_id", "receiver_id", "persona", "cosine_sim_origin",
            "semantic_drift", "bert_score_f1", "nli_label", "hallucination_rate", "message"
        ])
        writer.writeheader()
        for row in hop_metrics:
            writer.writerow(row)

    # 7. Vẽ biểu đồ suy giảm ngữ nghĩa (Semantic Degradation Plot)
    chart_path = os.path.join(output_dir, "semantic_degradation_chart.png")
    hops = [m["hop"] for m in hop_metrics]
    cos_sims = [m["cosine_sim_origin"] for m in hop_metrics]
    bert_f1s = [m["bert_score_f1"] for m in hop_metrics]
    drifts = [m["semantic_drift"] for m in hop_metrics]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(hops, cos_sims, marker="o", linewidth=2.5, color="#2563eb", label="Cosine Similarity (Sentence Embeddings)")
    plt.plot(hops, bert_f1s, marker="s", linewidth=2.2, color="#10b981", linestyle="--", label="BERTScore F1 (Token Contextual)")
    plt.plot(hops, drifts, marker="^", linewidth=2.0, color="#ef4444", linestyle=":", label="Semantic Drift Distance (1 - CosSim)")

    plt.title(f"Sự Suy Giảm Ngữ Nghĩa Qua Các Bước Nhảy Trên Mạng Vòng (Ring Topology, N={num_nodes})\nĐề tài NCKH 2026 Nhóm 1 - GVHD: TS. Phạm Ngọc Hưng", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Số bước nhảy truyền tiếp (Hops)", fontsize=10)
    plt.ylabel("Giá trị chỉ số đo lường", fontsize=10)
    plt.xticks(hops)
    plt.ylim(-0.05, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="best", frameon=True, shadow=True)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    print("="*70)
    print("[SUCCESS] HOÀN THÀNH MÔ PHỎNG THỰC NGHIỆM TRUYỀN TIN SƠ BỘ!")
    print(f"[FILE] Tệp nhật ký hội thoại: {txt_log_path}")
    print(f"[DATA] Tệp số liệu thực nghiệm: {csv_path}")
    print(f"[PLOT] Biểu đồ suy giảm ngữ nghĩa: {chart_path}")
    print("="*70)

    return {
        "txt_log": txt_log_path,
        "csv": csv_path,
        "chart": chart_path,
        "final_cosine": cos_sims[-1],
        "final_bert_f1": bert_f1s[-1]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy thử nghiệm truyền tin sơ bộ mạng vòng Ring Topology (NCKH 2026)")
    parser.add_argument("--nodes", type=int, default=5, help="Số lượng tác tử (3 đến 5)")
    parser.add_argument("--model-type", type=str, default="MOCK", choices=["MOCK", "OLLAMA", "CLOUD", "DEEPSEEK"], help="Loại mô hình AI")
    parser.add_argument("--model-name", type=str, default="llama3:8b", help="Tên mô hình")
    parser.add_argument("--message", type=str, default="Tổ chức Y tế Thế giới (WHO) khuyến cáo tiêm chủng đầy đủ để phòng ngừa các biến thể cúm mùa trong năm 2026.", help="Thông điệp gốc")

    args = parser.parse_args()

    asyncio.run(run_ring_propagation(
        num_nodes=args.nodes,
        model_type=args.model_type,
        model_name=args.model_name,
        seed_message=args.message
    ))
