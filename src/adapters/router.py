from typing import Dict, Any, List, Optional
from src.adapters.base import BaseModelAdapter
from src.adapters.ollama_adapter import OllamaAdapter
from src.adapters.cloud_adapter import CloudAdapter
from src.adapters.mock_adapter import MockLLMAdapter

class ModelRouter:
    """
    Bộ điều phối mô hình dị thể (Heterogeneous Model Router).
    Định tuyến yêu cầu từ từng tác tử tới đúng backend (Ollama, Cloud, Mock).
    Tự động fallback sang Mock nếu Ollama hoặc Cloud chưa sẵn sàng để đảm bảo hệ thống không sập.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_default_model: str = "llama3:8b",
        openai_key: Optional[str] = None,
        gemini_key: Optional[str] = None
    ):
        self.ollama = OllamaAdapter(base_url=ollama_url, default_model=ollama_default_model)
        self.cloud = CloudAdapter(openai_key=openai_key, gemini_key=gemini_key)
        self.mock = MockLLMAdapter()
        self._ollama_online: Optional[bool] = None
        self._last_check_time: float = 0.0
        self._cache_ttl: float = 5.0

    async def is_ollama_available(self) -> bool:
        """Kiểm tra có đệm (cached) trạng thái Ollama."""
        import time
        now = time.time()
        if self._ollama_online is not None and (now - self._last_check_time) < self._cache_ttl:
            return self._ollama_online
        
        health = await self.ollama.health_check()
        self._ollama_online = bool(health.get("online"))
        self._last_check_time = now
        return self._ollama_online

    async def check_all_providers(self) -> Dict[str, Any]:
        """
        Lấy trạng thái kết nối của toàn bộ hệ sinh thái mô hình AI.
        """
        ollama_status = await self.ollama.health_check()
        self._ollama_online = bool(ollama_status.get("online"))
        cloud_status = await self.cloud.health_check()
        mock_status = await self.mock.health_check()

        return {
            "ollama": ollama_status,
            "cloud": cloud_status,
            "mock": mock_status,
            "recommended_mode": "OLLAMA" if ollama_status.get("online") else ("CLOUD" if cloud_status.get("cloud_ready") else "MOCK")
        }

    def get_adapter(self, model_type: str) -> BaseModelAdapter:
        """
        Lấy adapter tương ứng theo loại mô hình yêu cầu.
        """
        model_type_upper = (model_type or "MOCK").upper()
        if model_type_upper == "OLLAMA":
            return self.ollama
        elif model_type_upper in ["CLOUD", "OPENAI", "GEMINI"]:
            return self.cloud
        return self.mock

    async def generate_for_agent(
        self,
        model_type: str,
        model_name: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = 42
    ) -> str:
        """
        Gọi sinh văn bản với cơ chế fallback tự động.
        """
        adapter = self.get_adapter(model_type)

        try:
            if model_type.upper() == "OLLAMA":
                # Kiểm tra nhanh kết nối Ollama có đệm
                is_online = await self.is_ollama_available()
                if not is_online:
                    # Fallback sang Mock kèm cảnh báo
                    return await self.mock.generate(prompt=prompt, system=system, temperature=temperature, seed=seed)
                return await self.ollama.generate(
                    prompt=prompt, system=system, temperature=temperature, seed=seed, model=model_name
                )
            elif model_type.upper() in ["CLOUD", "OPENAI", "GEMINI", "DEEPSEEK"]:
                health = await self.cloud.health_check()
                if not health.get("cloud_ready"):
                    return await self.mock.generate(prompt=prompt, system=system, temperature=temperature, seed=seed)
                
                # Tự động chọn DeepSeek, Gemini hoặc OpenAI dựa trên model_name và API key có sẵn
                if "deepseek" in model_name.lower() or model_type.upper() == "DEEPSEEK":
                    provider = "deepseek"
                elif "gemini" in model_name.lower() or model_type.upper() == "GEMINI":
                    provider = "gemini"
                elif "gpt" in model_name.lower() or model_type.upper() == "OPENAI":
                    provider = "openai"
                elif self.cloud.deepseek_key:
                    provider = "deepseek"
                elif self.cloud.gemini_key and not self.cloud.openai_key:
                    provider = "gemini"
                else:
                    provider = "openai" if self.cloud.openai_key else ("deepseek" if self.cloud.deepseek_key else "gemini")

                return await self.cloud.generate(
                    prompt=prompt, system=system, temperature=temperature, seed=seed, provider=provider
                )
            else:
                return await self.mock.generate(prompt=prompt, system=system, temperature=temperature, seed=seed)

        except Exception as e:
            # Nếu có bất kỳ lỗi nào từ API thực tế, fallback an toàn sang Mock
            print(f"[ModelRouter Warning] Lỗi gọi {model_type} ({str(e)}). Tự động fallback sang Mock LLM.")
            return await self.mock.generate(prompt=prompt, system=system, temperature=temperature, seed=seed)

    async def embed_text(self, text: str, preferred_type: str = "OLLAMA") -> List[float]:
        """
        Trích xuất vector embedding phục vụ tính Semantic Drift.
        """
        if preferred_type.upper() == "OLLAMA":
            is_online = await self.is_ollama_available()
            if not is_online:
                if self.cloud.gemini_key or self.cloud.openai_key:
                    try:
                        return await self.cloud.embed(text)
                    except Exception:
                        pass
                return await self.mock.embed(text)
        adapter = self.get_adapter(preferred_type)
        try:
            return await adapter.embed(text)
        except Exception:
            return await self.mock.embed(text)
