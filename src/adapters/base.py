from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseModelAdapter(ABC):
    """
    Interface trừu tượng cho tất cả các nhà cung cấp LLM (Ollama, Cloud, Mock).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = 42,
        **kwargs
    ) -> str:
        """
        Sinh phản hồi văn bản từ mô hình ngôn ngữ.
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Trích xuất vector đặc trưng ngữ nghĩa của văn bản.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái kết nối tới nhà cung cấp mô hình.
        """
        pass
