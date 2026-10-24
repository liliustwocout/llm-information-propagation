import os
import json
import csv
import time
from typing import Dict, Any, List, Optional

class TelemetryManager:
    """
    Quản lý lưu vết thực nghiệm (Provenance & Telemetry), xuất dữ liệu chuẩn
    phục vụ viết bài báo khoa học, phân tích thống kê ANOVA và vẽ đồ thị.
    """

    def __init__(self, output_dir: str = "experiments"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_experiment_run(
        self,
        simulation_id: str,
        config: Dict[str, Any],
        hop_metrics: List[Dict[str, Any]],
        all_traces: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Lưu toàn bộ kết quả một đợt chạy thực nghiệm ra các tệp JSON và CSV.
        """
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        base_name = f"{simulation_id}_{timestamp_str}"

        # 1. Lưu tệp JSON tổng hợp
        json_path = os.path.join(self.output_dir, f"{base_name}_full.json")
        full_data = {
            "simulation_id": simulation_id,
            "config": config,
            "hop_metrics": hop_metrics,
            "traces": all_traces
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        # 2. Lưu tệp CSV chỉ số từng hop (cho SPSS, R, Python Pandas)
        metrics_csv_path = os.path.join(self.output_dir, f"{base_name}_hop_metrics.csv")
        if hop_metrics:
            fieldnames = list(hop_metrics[0].keys())
            with open(metrics_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in hop_metrics:
                    writer.writerow(row)

        # 3. Lưu tệp CSV trace từng thông điệp
        traces_csv_path = os.path.join(self.output_dir, f"{base_name}_message_traces.csv")
        if all_traces:
            trace_keys = [
                "simulation_id", "hop", "sender_id", "agent_id", "persona",
                "model_type", "model_name", "decision", "belief_score",
                "drift_distance", "cosine_similarity", "nli_label", "hallucination_rate",
                "bert_f1", "incoming_message", "outgoing_message", "reasoning",
                "reflection_enabled", "reflection_critique", "reflection_hallucination_detected",
                "consensus_protocol", "consensus_status", "consensus_details"
            ]
            with open(traces_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=trace_keys, extrasaction="ignore")
                writer.writeheader()
                for t in all_traces:
                    row = dict(t)
                    # Flatten self_reflection dict
                    ref = t.get("self_reflection") or {}
                    row["reflection_enabled"] = ref.get("enabled", False)
                    row["reflection_critique"] = ref.get("critique", "")
                    row["reflection_hallucination_detected"] = ref.get("hallucination_detected", False)
                    # Flatten consensus dict
                    con = t.get("consensus") or {}
                    row["consensus_protocol"] = con.get("protocol", "NONE")
                    row["consensus_status"] = con.get("status", "NONE")
                    row["consensus_details"] = con.get("details", "")
                    writer.writerow(row)

        return {
            "json_path": json_path,
            "metrics_csv": metrics_csv_path,
            "traces_csv": traces_csv_path
        }
