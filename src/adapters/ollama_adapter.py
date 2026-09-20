import httpx
import asyncio
from typing import Dict, Any, List, Optional
from src.adapters.base import BaseModelAdapter
from src.core.metrics import MetricsCalculator

class OllamaAdapter(BaseModelAdapter):
    """
    Adapter kết nối trực tiếp tới máy chủ Ollama cục bộ (http://localhost:11434).
    Tích hợp Semaphore để kiểm soát số lượng luồng đồng thời, bảo vệ GPU/VRAM.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3:8b",
        embed_model: str = "nomic-embed-text",
        max_concurrency: int = 2,
        timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.embed_model = embed_model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout = timeout if timeout != 60.0 else 180.0

    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái kết nối và lấy danh sách mô hình đã tải về máy.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "online": True,
                        "base_url": self.base_url,
                        "available_models": models,
                        "has_default_model": any(self.default_model in m for m in models),
                        "message": f"Kết nối Ollama thành công ({len(models)} mô hình sẵn sàng)"
                    }
        except Exception as e:
            return {
                "online": False,
                "base_url": self.base_url,
                "available_models": [],
                "has_default_model": False,
                "message": f"Chưa kết nối được Ollama: {str(e)}"
            }

        return {
            "online": False,
            "base_url": self.base_url,
            "available_models": [],
            "has_default_model": False,
            "message": "Không nhận được phản hồi từ Ollama"
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = 42,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Gửi yêu cầu sinh văn bản tới Ollama kèm cơ chế hàng đợi bảo vệ VRAM.
        """
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(temperature),
                "seed": int(seed) if seed is not None else 42,
                "num_predict": kwargs.get("max_tokens", 250)
            }
        }
        if system:
            payload["system"] = system

        async with self.semaphore:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    if response.status_code == 200:
                        return response.json().get("response", "")
                    else:
                        raise RuntimeError(f"Ollama trả về lỗi {response.status_code}: {response.text}")
                except Exception as e:
                    raise RuntimeError(f"Lỗi khi gọi mô hình Ollama ({target_model}): {str(e)}")

    async def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Trích xuất vector embedding từ Ollama. Tự động fallback sang thuật toán nhẹ nếu lỗi.
        """
        target_model = model or self.embed_model
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # 1. Thử endpoint /api/embed chuẩn mới (Ollama v0.3+)
                res = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": target_model, "input": text}
                )
                if res.status_code == 200:
                    data = res.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0]

                # 2. Thử endpoint /api/embeddings cũ
                res_old = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": target_model, "prompt": text}
                )
                if res_old.status_code == 200:
                    data_old = res_old.json()
                    embedding = data_old.get("embedding", [])
                    if embedding:
                        return embedding
        except Exception:
            pass

        # Fallback sang thuật toán nhẹ để thí nghiệm không bị gián đoạn
        return MetricsCalculator.compute_lightweight_embedding(text)
