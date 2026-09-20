import os
import httpx
from typing import Dict, Any, List, Optional
from src.adapters.base import BaseModelAdapter
from src.core.metrics import MetricsCalculator

class CloudAdapter(BaseModelAdapter):
    """
    Adapter kết nối các mô hình Cloud AI (OpenAI GPT-4o, Google Gemini) thông qua REST API.
    """

    def __init__(
        self,
        openai_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        gemini_key: Optional[str] = None,
        gemini_model: str = "gemini-1.5-flash"
    ):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY", "")
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = gemini_model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra tính hợp lệ của các API keys.
        """
        has_openai = bool(self.openai_key and len(self.openai_key.strip()) > 10)
        has_gemini = bool(self.gemini_key and len(self.gemini_key.strip()) > 10)

        return {
            "openai_configured": has_openai,
            "openai_model": self.openai_model if has_openai else None,
            "gemini_configured": has_gemini,
            "gemini_model": self.gemini_model if has_gemini else None,
            "cloud_ready": has_openai or has_gemini,
            "message": "Cloud API đã sẵn sàng" if (has_openai or has_gemini) else "Chưa cấu hình API key Cloud (tùy chọn)"
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = 42,
        provider: str = "openai",
        **kwargs
    ) -> str:
        """
        Gọi API OpenAI hoặc Gemini để sinh phản hồi.
        """
        if provider == "gemini" and self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system or ''}\n\n{prompt}"}]}],
                "generationConfig": {
                    "temperature": float(temperature),
                    "maxOutputTokens": kwargs.get("max_tokens", 250)
                }
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"]
                raise RuntimeError(f"Gemini API Error: {res.status_code} - {res.text}")

        # Mặc định gọi OpenAI
        if self.openai_key:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.openai_model,
                "messages": messages,
                "temperature": float(temperature),
                "seed": int(seed) if seed is not None else 42,
                "max_tokens": kwargs.get("max_tokens", 250)
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                raise RuntimeError(f"OpenAI API Error: {res.status_code} - {res.text}")

        raise ValueError("Chưa cấu hình API key hợp lệ cho Cloud Provider")

    async def embed(self, text: str) -> List[float]:
        """
        Trích xuất vector embedding qua OpenAI hoặc fallback sang thuật toán nhẹ.
        """
        if self.openai_key:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": text,
                "model": "text-embedding-3-small"
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
                    if res.status_code == 200:
                        return res.json()["data"][0]["embedding"]
            except Exception:
                pass

        return MetricsCalculator.compute_lightweight_embedding(text)
