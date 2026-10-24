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
        prompt_upper = (prompt + " " + (system or "")).upper()
        for p in ["FACT_CHECKER", "GULLIBLE_SPREADER", "DOGMATIC_PARTISAN", "OPINION_LEADER", "MALICIOUS_SPREADER"]:
            if p in prompt_upper:
                persona = p
                break

        # 1. Xử lý phản hồi Tự phản tư (Self-Reflection Task)
        if "[SELF-REFLECTION" in prompt:
            draft_msg = ""
            if "[YOUR DRAFT MESSAGE]" in prompt:
                try:
                    draft_msg = prompt.split('[YOUR DRAFT MESSAGE]')[1].split('"""')[1].strip()
                except Exception:
                    draft_msg = "Thông điệp dự thảo"

            has_halu = any(w in draft_msg.lower() for w in ["khẩn cấp", "chấn động", "kẻo bị xóa", "che giấu", "biến chứng", "thần dược"])
            if has_halu:
                critique = "Tự phản tư: Phát hiện chi tiết phóng đại và từ ngữ giật gân chưa kiểm chứng. Cần tinh chỉnh giảm thiểu ảo giác."
                sanitized = draft_msg.replace("Cực kỳ khẩn cấp bà con ơi! ", "").replace("Mọi người xem ngay kẻo bị xóa: ", "").replace("Tin chấn động vừa được tiết lộ: ", "")
                sanitized = sanitized.replace(" và các chuyên gia đang âm thầm che giấu sự việc.", "").replace(" và các chuyên gia đang âm thầm che giấu sự việc", "")
                revised = sanitized.strip()
            else:
                critique = "Tự phản tư: Thông điệp trung thực và bám sát nguồn tin gốc, không phát hiện ảo giác."
                revised = draft_msg

            return json.dumps({
                "critique": critique,
                "hallucination_detected": has_halu,
                "revised_outgoing_message": revised
            }, ensure_ascii=False)

        # 2. Xử lý phản hồi Thẩm định chéo (Peer Review Task)
        if "[PEER REVIEW" in prompt:
            cand_msg = ""
            if "[CANDIDATE MESSAGE]" in prompt:
                try:
                    cand_msg = prompt.split('[CANDIDATE MESSAGE]')[1].split('"""')[1].strip()
                except Exception:
                    cand_msg = "Thông điệp ứng viên"

            is_suspicious = any(w in cand_msg.lower() for w in ["chấn động", "bị xóa", "che giấu", "thần dược", "đột quỵ"])
            if is_suspicious and persona in ["FACT_CHECKER", "OPINION_LEADER"]:
                verdict = "DISPUTE"
                comment = "Phản biện: Thông điệp mang tính giật gân, thiếu căn cứ y khoa chính thống."
                conf = 0.85
            else:
                verdict = "APPROVE"
                comment = "Đồng thuận: Thông điệp hợp lệ để chia sẻ trong mạng lưới."
                conf = 0.90

            return json.dumps({
                "verdict": verdict,
                "confidence": conf,
                "review_comment": comment
            }, ensure_ascii=False)

        # Trích xuất đoạn tin nhắn
        msg_content = "Thông tin ban đầu"
        if '"""' in prompt:
            parts = prompt.split('"""')
            if len(parts) >= 2:
                msg_content = parts[1].strip()

        # Tạo phản hồi và biến dạng ngữ nghĩa theo Persona
        if persona == "FACT_CHECKER":
            dubious_keywords = ["tin giả", "đột quỵ", "thần dược", "bí mật", "chấn động", "khẩn cấp", "che giấu", "nguy hiểm", "biến chứng", "bị xóa", "phe chúng ta", "bà con ơi"]
            is_dubious = any(k in msg_content.lower() for k in dubious_keywords)
            decision = "COUNTER" if is_dubious else "FORWARD"
            if decision == "COUNTER":
                reasoning = "Nội dung chứa nhiều từ ngữ giật gân, thiếu chứng cứ khoa học xác thực hoặc có dấu hiệu phóng đại thông tin."
                belief = -0.75
                clean_preview = msg_content.replace("Ghi nhận: ", "")[:60]
                outgoing = f"CẢNH BÁO KIỂM CHỨNG: Nhận định '{clean_preview}...' chưa có cơ sở khoa học xác thực. Khuyến cáo mọi người đối chiếu nguồn tài liệu y tế chính thống."
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
                # Không lặp tiền tố nếu đã có
                outgoing = msg_content if msg_content.startswith("Ghi nhận: ") else f"Ghi nhận: {msg_content}"

        result = {
            "reasoning": reasoning,
            "decision": decision,
            "updated_belief": round(belief, 3),
            "outgoing_message": outgoing
        }
        return json.dumps(result, ensure_ascii=False)

    async def embed(self, text: str) -> List[float]:
        return MetricsCalculator.compute_lightweight_embedding(text)
