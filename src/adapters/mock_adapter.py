import random
import json
from typing import Dict, Any, List, Optional
from src.adapters.base import BaseModelAdapter
from src.core.metrics import MetricsCalculator

class MockLLMAdapter(BaseModelAdapter):
    """
    Bộ giả lập nhận thức LLM thông minh (Mock Provider).
    Mô phỏng chân thực các đột biến ngữ nghĩa (Semantic Drift), ảo giác và hành vi tâm lý
    của các Persona khác nhau, giúp chạy thử nghiệm hệ thống ngay lập tức mà không phụ thuộc phần cứng.
    """

    def __init__(self):
        self.rng = random.Random(42)

    async def health_check(self) -> Dict[str, Any]:
        return {
            "online": True,
            "mock_mode": True,
            "message": "Chế độ Mô phỏng / Mock LLM luôn sẵn sàng cho kiểm thử nhanh"
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = 42,
        **kwargs
    ) -> str:
        """
        Sinh phản hồi giả lập có cấu trúc JSON hợp lệ tuân theo Persona của tác tử.
        """
        if seed is not None:
            self.rng.seed(seed + hash(prompt) % 10000)

        # Trích xuất nội dung tin nhắn và Persona từ prompt
        persona = "NEUTRAL_OBSERVER"
        for p in ["FACT_CHECKER", "GULLIBLE_SPREADER", "DOGMATIC_PARTISAN", "OPINION_LEADER", "MALICIOUS_SPREADER"]:
            if p in (system or "") or p in prompt:
                persona = p
                break

        # Trích xuất đoạn tin nhắn
        msg_content = "Thông tin ban đầu"
        if '"""' in prompt:
            parts = prompt.split('"""')
            if len(parts) >= 2:
                msg_content = parts[1].strip()

        # Tạo phản hồi và biến dạng ngữ nghĩa theo Persona
        if persona == "FACT_CHECKER":
            decision = "COUNTER" if ("tin giả" in msg_content.lower() or "đột quỵ" in msg_content.lower() or "thần dược" in msg_content.lower() or "bí mật" in msg_content.lower()) else "FORWARD"
            if decision == "COUNTER":
                reasoning = "Nội dung chứa nhiều từ ngữ giật gân, thiếu chứng cứ khoa học xác thực."
                belief = -0.75
                outgoing = f"CẢNH BÁO KIỂM CHỨNG: Nhận định sau đây chưa có cơ sở khoa học: '{msg_content[:60]}...'. Khuyến cáo mọi người đối chiếu nguồn tài liệu y tế chính thống."
            else:
                reasoning = "Dữ liệu phù hợp với các báo cáo khoa học đã công bố."
                belief = 0.8
                outgoing = f"XÁC NHẬN: Thông tin khoa học chuẩn xác: {msg_content}"

        elif persona == "GULLIBLE_SPREADER":
            decision = "FORWARD"
            reasoning = "Thông tin quá bất ngờ và chấn động! Cần chia sẻ ngay cho cộng đồng."
            belief = min(1.0, 0.6 + self.rng.uniform(0.1, 0.35))
            exaggerations = [
                "Tin chấn động vừa được tiết lộ: ",
                "Mọi người xem ngay kẻo bị xóa: ",
                "Cực kỳ khẩn cấp bà con ơi! "
            ]
            outgoing = f"{self.rng.choice(exaggerations)}{msg_content}! Ai cũng phải biết điều này!"

        elif persona == "DOGMATIC_PARTISAN":
            decision = "FORWARD"
            reasoning = "Thông điệp này củng cố tuyệt đối lập trường của chúng ta."
            belief = 0.95
            outgoing = f"Đúng như phe chúng ta đã khẳng định từ trước: {msg_content}. Bất kỳ ai phản đối đều có động cơ xấu!"

        elif persona == "OPINION_LEADER":
            decision = "FORWARD"
            reasoning = "Đây là chủ đề đáng chú ý, cần phân tích sâu hơn để định hướng dư luận."
            belief = 0.5
            outgoing = f"Góc nhìn chuyên gia: Về vấn đề '{msg_content[:50]}...', chúng ta cần xem xét đa chiều giữa dữ liệu thống kê và bối cảnh thực tiễn."

        elif persona == "MALICIOUS_SPREADER":
            decision = "FORWARD"
            reasoning = "Thêm một chút chi tiết ngụy tạo để kích thích sự sợ hãi và tranh cãi."
            belief = -0.2
            rumor_injections = [
                " và các chuyên gia đang âm thầm che giấu sự việc",
                " nhưng chính quyền không muốn dân biết sự thật",
                " và đã có hàng nghìn trường hợp gặp biến chứng nguy hiểm"
            ]
            outgoing = f"{msg_content}{self.rng.choice(rumor_injections)}."

        else: # NEUTRAL_OBSERVER
            if self.rng.random() < 0.65:
                decision = "IGNORE"
                reasoning = "Nội dung chưa đủ tính thuyết phục hoặc không cần thiết phải chuyển tiếp."
                belief = 0.0
                outgoing = ""
            else:
                decision = "FORWARD"
                reasoning = "Chuyển tiếp nguyên văn một cách thận trọng."
                belief = 0.1
                outgoing = f"Ghi nhận: {msg_content}"

        result = {
            "reasoning": reasoning,
            "decision": decision,
            "updated_belief": round(belief, 3),
            "outgoing_message": outgoing
        }
        return json.dumps(result, ensure_ascii=False)

    async def embed(self, text: str) -> List[float]:
        return MetricsCalculator.compute_lightweight_embedding(text)
