import os
import httpx
from typing import Dict, Any, List, Optional
from src.adapters.base import BaseModelAdapter
from src.core.metrics import MetricsCalculator

class CloudAdapter(BaseModelAdapter):
    """
    Adapter kết nối các mô hình Cloud AI (OpenAI GPT-4o, Google Gemini, DeepSeek) thông qua REST API.
    """

    def __init__(
        self,
        openai_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        gemini_key: Optional[str] = None,
        gemini_model: str = "gemini-3.5-flash-lite",
        deepseek_key: Optional[str] = None,
        deepseek_model: str = "deepseek-chat"
    ):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY", "")
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = gemini_model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.deepseek_key = deepseek_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_model = deepseek_model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra tính hợp lệ của các API keys.
        """
        has_openai = bool(self.openai_key and len(self.openai_key.strip()) > 10)
        has_gemini = bool(self.gemini_key and len(self.gemini_key.strip()) > 10)
        has_deepseek = bool(self.deepseek_key and len(self.deepseek_key.strip()) > 10)

        return {
            "openai_configured": has_openai,
            "openai_model": self.openai_model if has_openai else None,
            "gemini_configured": has_gemini,
            "gemini_model": self.gemini_model if has_gemini else None,
            "deepseek_configured": has_deepseek,
            "deepseek_model": self.deepseek_model if has_deepseek else None,
            "cloud_ready": has_openai or has_gemini or has_deepseek,
            "message": "Cloud API đã sẵn sàng" if (has_openai or has_gemini or has_deepseek) else "Chưa cấu hình API key Cloud (tùy chọn)"
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
        Gọi API DeepSeek, OpenAI hoặc Gemini để sinh phản hồi.
        """
        provider_lower = provider.lower()
        use_deepseek = (provider_lower in ["deepseek", "deepseek-chat"]) or (bool(self.deepseek_key) and not bool(self.openai_key) and not bool(self.gemini_key))

        # 1. Gọi DeepSeek API (OpenAI compatible endpoint)
        if use_deepseek and self.deepseek_key:
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.deepseek_model,
                "messages": messages,
                "temperature": float(temperature),
                "max_tokens": kwargs.get("max_tokens", 250)
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                raise RuntimeError(f"DeepSeek API Error: {res.status_code} - {res.text}")

        # 2. Gọi Gemini API
        use_gemini = (provider_lower == "gemini") or (bool(self.gemini_key) and not bool(self.openai_key))
        if use_gemini and self.gemini_key:
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
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                raise RuntimeError(f"Gemini API Error: {res.status_code} - {res.text}")

        # 3. Mặc định gọi OpenAI nếu có key
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

        raise ValueError("Chưa cấu hình API key hợp lệ cho Cloud Provider (DeepSeek, OpenAI hoặc Gemini)")

    async def embed(self, text: str) -> List[float]:
        """
        Trích xuất vector embedding qua OpenAI hoặc Gemini hoặc fallback sang thuật toán nhẹ.
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
        elif self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={self.gemini_key}"
            payload = {
                "content": {"parts": [{"text": text[:2000]}]}
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        values = res.json().get("embedding", {}).get("values", [])
                        if values:
                            return values
            except Exception:
                pass

        return MetricsCalculator.compute_lightweight_embedding(text)
