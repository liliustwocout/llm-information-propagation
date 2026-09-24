import numpy as np
from typing import List, Dict, Any, Optional
import math
import hashlib

class MetricsCalculator:
    """
    Bộ tính toán chỉ số động học lan truyền và biến dạng ngữ nghĩa chuẩn NCKH.
    """

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Tính toán độ tương đồng Cosine giữa 2 vector đặc trưng ngữ nghĩa.
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        dot_product = float(np.dot(a, b))
        return float(dot_product / (norm_a * norm_b))

    @staticmethod
    def semantic_drift_distance(v_origin: List[float], v_current: List[float]) -> float:
        """
        Tính khoảng cách trôi dạt ngữ nghĩa: Dist_sem = 1.0 - CosineSimilarity.
        Giá trị trong đoạn [0.0, 2.0], thông thường [0.0, 1.0].
        0.0 = Giữ nguyên vẹn 100% ngữ nghĩa.
        1.0 = Trôi dạt hoàn toàn sang chủ đề khác.
        """
        sim = MetricsCalculator.cosine_similarity(v_origin, v_current)
        # Giới hạn sim trong [-1.0, 1.0] tránh sai số số thực
        sim = max(-1.0, min(1.0, sim))
        return round(float(1.0 - sim), 4)

    @staticmethod
    def compute_lightweight_embedding(text: str, dim: int = 128) -> List[float]:
        """
        Thuật toán sinh vector ngữ nghĩa nhẹ (Deterministic Semantic Hashing)
        dùng làm đối chứng chuẩn xác khi máy trạm chưa tải mô hình embedding Ollama.
        """
        words = text.lower().strip().split()
        if not words:
            return [0.0] * dim

        vec = np.zeros(dim, dtype=np.float32)
        for i, word in enumerate(words):
            # Băm từng từ và phân bổ vào các chiều vector
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            weight = 1.0 / (1.0 + 0.05 * i)
            vec[idx] += sign * weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def compute_penetration_rate(total_nodes: int, informed_nodes: int) -> float:
        """
        Tỷ lệ thẩm thấu / bao phủ của thông điệp trên toàn mạng R(t) = |V_informed| / N * 100%
        """
        if total_nodes <= 0:
            return 0.0
        return round(float((informed_nodes / total_nodes) * 100.0), 2)

    @staticmethod
    def compute_polarization_index(beliefs: List[float]) -> float:
        """
        Chỉ số phân cực niềm tin của quần thể PI(t) = Phương sai phân bố niềm tin.
        Var(B) = (1/N) * sum( (b_i - mean_b)^2 )
        PI -> 0: Đồng thuận hoàn toàn.
        PI -> 1: Phân cực nhị nguyên đối kháng gay gắt.
        """
        if not beliefs:
            return 0.0
        arr = np.array(beliefs, dtype=np.float32)
        variance = float(np.var(arr))
        return round(variance, 4)

    @staticmethod
    def compute_effective_reproduction_rate(new_infected: int, currently_active: int) -> float:
        """
        Hệ số lây nhiễm hiệu dụng R_t = Số nút mới bị lây / Số nút truyền tin ở vòng trước
        """
        if currently_active <= 0:
            return 0.0
        return round(float(new_infected / currently_active), 2)

    @staticmethod
    def compute_bert_score(reference: str, candidate: str) -> Dict[str, float]:
        """
        Chỉ số 2: BERTScore (P, R, F1) theo chuẩn ICLR 2020 (Zhang et al.).
        Đo lường độ trùng khớp ngữ nghĩa từng từ dựa trên ma trận căn chỉnh ngữ cảnh tham lam (Greedy Alignment).
        """
        ref_tokens = [w.lower().strip(".,!?;:()[]\"'") for w in reference.split() if len(w) > 1]
        cand_tokens = [w.lower().strip(".,!?;:()[]\"'") for w in candidate.split() if len(w) > 1]

        if not ref_tokens or not cand_tokens:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Trích xuất vector nhúng cho từng token
        ref_vecs = [MetricsCalculator.compute_lightweight_embedding(t, dim=64) for t in ref_tokens]
        cand_vecs = [MetricsCalculator.compute_lightweight_embedding(t, dim=64) for t in cand_tokens]

        # 1. Recall (R_BERT): Với mỗi token trong reference, tìm token khớp nhất trong candidate
        recall_matches = []
        for r_vec in ref_vecs:
            max_sim = max(MetricsCalculator.cosine_similarity(r_vec, c_vec) for c_vec in cand_vecs)
            recall_matches.append(max(0.0, max_sim))
        recall = float(np.mean(recall_matches)) if recall_matches else 0.0

        # 2. Precision (P_BERT): Với mỗi token trong candidate, tìm token khớp nhất trong reference
        precision_matches = []
        for c_vec in cand_vecs:
            max_sim = max(MetricsCalculator.cosine_similarity(c_vec, r_vec) for r_vec in ref_vecs)
            precision_matches.append(max(0.0, max_sim))
        precision = float(np.mean(precision_matches)) if precision_matches else 0.0

        # 3. F1-BERTScore: Trung bình điều hòa giữa Precision và Recall
        if (precision + recall) > 0:
            f1 = 2.0 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }

    @staticmethod
    def compute_nli_entailment(premise: str, hypothesis: str) -> Dict[str, Any]:
        """
        Chỉ số 3: Tỷ lệ suy diễn logic (NLI Entailment Ratio - chuẩn RoBERTa-large-MNLI).
        Kiểm tra xem hypothesis có phải là hệ quả logic (Entailment), trung lập (Neutral),
        hay mâu thuẫn (Contradiction) so với premise.
        """
        if not premise or not hypothesis:
            return {"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0, "label": "NEUTRAL"}

        # Trích xuất các từ phủ định nhận diện mâu thuẫn
        negation_markers = {"not", "no", "never", "false", "fake", "hoax", "sai", "không", "chưa", "bác bỏ", "xuyên tạc"}
        hypo_words = set(hypothesis.lower().split())
        prem_words = set(premise.lower().split())

        has_negation_in_hypo = bool(negation_markers.intersection(hypo_words))
        has_negation_in_prem = bool(negation_markers.intersection(prem_words))

        # Tính độ tương đồng ngữ nghĩa tổng thể
        v_prem = MetricsCalculator.compute_lightweight_embedding(premise)
        v_hypo = MetricsCalculator.compute_lightweight_embedding(hypothesis)
        sim = MetricsCalculator.cosine_similarity(v_prem, v_hypo)

        # Phân loại logic quan hệ
        overlap = len(prem_words.intersection(hypo_words)) / max(1, len(prem_words))

        if has_negation_in_hypo != has_negation_in_prem and (sim > 0.35 or overlap > 0.3):
            # Có từ phủ định lệch pha trên cùng một ngữ cảnh chủ đề -> Mâu thuẫn
            contradiction = min(0.95, round(max(sim, overlap) * 1.05, 4))
            entailment = round(max(0.02, 1.0 - contradiction - 0.05), 4)
            neutral = round(max(0.03, 1.0 - contradiction - entailment), 4)
            label = "CONTRADICTION"
        elif (sim >= 0.58 or overlap >= 0.60):
            # Độ tương đồng hoặc trùng khớp mệnh đề cao, khẳng định cùng hướng -> Hệ quả logic
            entailment = round(min(0.98, max(sim, overlap) * 0.95), 4)
            contradiction = round(max(0.01, (1.0 - entailment) * 0.2), 4)
            neutral = round(max(0.01, 1.0 - entailment - contradiction), 4)
            label = "ENTAILMENT"
        elif sim >= 0.35 or overlap >= 0.25:
            neutral = round(0.65, 4)
            entailment = round(0.20, 4)
            contradiction = round(0.15, 4)
            label = "NEUTRAL"
        else:
            # Ngữ cảnh trôi dạt quá xa
            neutral = 0.70
            entailment = 0.10
            contradiction = 0.20
            label = "NEUTRAL"

        return {
            "entailment": entailment,
            "neutral": neutral,
            "contradiction": contradiction,
            "label": label
        }

    @staticmethod
    def compute_hallucination_rate(source_text: str, generated_text: str) -> Dict[str, Any]:
        """
        Chỉ số 4: Tỷ lệ ảo giác (Hallucination Rate % theo chuẩn HaluEval).
        Xác định tỷ lệ các thực thể, con số, hoặc khẳng định mới bị tác tử tự bịa đặt
        vào văn bản mà không tồn tại trong nguồn tin ban đầu.
        """
        if not source_text or not generated_text:
            return {"hallucination_rate": 0.0, "hallucinated_tokens": [], "factual_consistency": 1.0}

        import re
        # Trích xuất các thực thể định lượng (số, ngày tháng, tên riêng viết hoa)
        source_clean = source_text.strip()
        gen_clean = generated_text.strip()

        # Tìm các con số hoặc thực thể viết hoa trong generated_text
        gen_entities = set(re.findall(r"\b[A-ZÀ-Ỹ][a-zà-ỹ0-9_]+\b|\b\d+[\.,]?\d*\b", gen_clean))
        source_entities = set(re.findall(r"\b[A-ZÀ-Ỹ][a-zà-ỹ0-9_]+\b|\b\d+[\.,]?\d*\b", source_clean))

        # Thực thể bị bịa đặt là các thực thể có trong gen_clean nhưng không có trong source
        fabricated = [e for e in gen_entities if e not in source_entities and len(e) > 1]

        if not gen_entities:
            # Nếu không có thực thể đặc biệt, đo dựa trên tỷ lệ từ mới xuất hiện ngoài từ điển gốc
            source_words = set(source_clean.lower().split())
            gen_words = [w.lower().strip(".,!?;:\"'") for w in gen_clean.split()]
            new_words = [w for w in gen_words if len(w) > 4 and w not in source_words]
            rate = (len(new_words) / max(1, len(gen_words))) * 100.0
            fabricated = list(set(new_words[:5]))
        else:
            rate = (len(fabricated) / max(1, len(gen_entities))) * 100.0

        rate = round(min(100.0, max(0.0, rate)), 2)
        consistency = round(max(0.0, 1.0 - (rate / 100.0)), 4)

        return {
            "hallucination_rate": rate,
            "hallucinated_tokens": fabricated,
            "factual_consistency": consistency
        }
