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
