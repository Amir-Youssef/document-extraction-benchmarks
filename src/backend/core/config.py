from __future__ import annotations

import os
from pathlib import Path

from backend.domain.enumx.llm_model import LLMModel

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

# Raiz do pacote fce-modulo5
_FCE_MODULO5_ROOT = Path(__file__).resolve().parents[3]


MODEL_IDENTIFIERS: dict[LLMModel, str] = {
    LLMModel.GEMINI_31_PRO: "gemini-3.1-pro-preview",
    LLMModel.GEMINI_FLASH: "gemini-3-flash-preview",
    LLMModel.VERTEX_AI: "vertex-ai-endpoint",
    LLMModel.GEMMA_3_27B: "gemma-3-27b-endpoint",
    LLMModel.GEMMA_3_12B: "gemma-3-12b-endpoint",
    LLMModel.KIMI_K2_5: "kimi-k2-5-endpoint",
    LLMModel.QWEN3_VL: "qwen3-vl-endpoint",
    LLMModel.QWEN_3_5_27B: "Qwen/Qwen3.5-27B",
    LLMModel.QWEN_3_5_35B: "Qwen/Qwen3.5-35B-A3B",
    LLMModel.QWEN_3_5_9B: "Qwen/Qwen3.5-9B",
    LLMModel.OLLAMA_GEMMA_3_12B: "gemma3:12b",
    LLMModel.OLLAMA_GEMMA_3_27B: "gemma3:27b",
    LLMModel.OLLAMA_QWEN3_VL: "qwen3-vl:latest",
    LLMModel.OLLAMA_QWEN3_VL_30B: "qwen3-vl:30b",
}

OLLAMA_VISION_MODELS: frozenset[LLMModel] = frozenset({
    LLMModel.OLLAMA_GEMMA_3_12B,
    LLMModel.OLLAMA_GEMMA_3_27B,
    LLMModel.OLLAMA_QWEN3_VL,
    LLMModel.OLLAMA_QWEN3_VL_30B,
})

VERTEX_MG_MODELS: frozenset[LLMModel] = frozenset({
    LLMModel.VERTEX_AI,
    LLMModel.GEMMA_3_27B,
    LLMModel.GEMMA_3_12B,
    LLMModel.KIMI_K2_5,
    LLMModel.QWEN3_VL,
    LLMModel.QWEN_3_5_27B,
    LLMModel.QWEN_3_5_35B,
    LLMModel.QWEN_3_5_9B,
    LLMModel.OLLAMA_GEMMA_3_12B,
    LLMModel.OLLAMA_GEMMA_3_27B,
    LLMModel.OLLAMA_QWEN3_VL,
    LLMModel.OLLAMA_QWEN3_VL_30B,
})


class Settings(BaseSettings):
    app_name: str = "Doc Extractor API"
    environment: str = "development"
    log_level: str = "INFO"
    gemini_api_key: str = Field(default="", min_length=1)
    default_llm_model: LLMModel = LLMModel.GEMINI_31_PRO

    # Vertex AI settings
    vertex_project_id: str = ""
    vertex_location: str = ""
    vertex_endpoint_id: str = ""
    vertex_model_name: str = ""

    # Multimodal / Vision - Endpoint IDs
    gemma_3_27b_endpoint_id: str = ""
    gemma_3_27b_location: str = ""
    gemma_3_27b_dedicated_domain: str = ""
    gemma_3_12b_endpoint_id: str = ""
    gemma_3_12b_location: str = ""
    gemma_3_12b_dedicated_domain: str = ""
    kimi_k2_5_endpoint_id: str = ""
    kimi_k2_5_location: str = ""
    kimi_k2_5_dedicated_domain: str = ""
    qwen3_vl_endpoint_id: str = ""
    qwen3_vl_location: str = ""
    qwen3_vl_dedicated_domain: str = ""

    # Qwen 3.5 (External vLLM)
    qwen_3_5_27b_url: str = "https://qwen35-27b.fce.4vants.com.br/v1/chat/completions"
    qwen_3_5_27b_api_key: str = "HUVLBT0jjlYLdCm0giuCWA"
    qwen_3_5_35b_url: str = "https://qwen35-35b.fce.4vants.com.br/v1/chat/completions"
    qwen_3_5_35b_api_key: str = "HUVLBT0jjlYLdCm0giuCWA"
    qwen_3_5_9b_url: str = "https://qwen35-9b.fce.4vants.com.br/v1/chat/completions"
    qwen_3_5_9b_api_key: str = "HUVLBT0jjlYLdCm0giuCWA"

    # Ollama settings
    ollama_base_url: str = ""
    ollama_api_key: str = ""
    ollama_model: str = "gemma3:12b"

    @model_validator(mode="after")
    def _ollama_api_key_from_env(self) -> Settings:
        key = (self.ollama_api_key or "").strip()
        if not key:
            key = (os.environ.get("OLLAMA_API_KEY") or "").strip()
        if key.lower().startswith("bearer "):
            key = key[7:].strip()
        object.__setattr__(self, "ollama_api_key", key)
        return self

    model_config = {
        "env_prefix": "DOC_EXTRACTOR_",
        "env_file": (
            Path.cwd() / ".env",
            _FCE_MODULO5_ROOT / ".env",
        ),
        "extra": "ignore",
    }


settings = Settings()
