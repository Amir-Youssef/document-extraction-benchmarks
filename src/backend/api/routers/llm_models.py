from fastapi import APIRouter
from pydantic import BaseModel

from backend.domain.enumx.llm_model import LLMModel

router = APIRouter(prefix="/v1", tags=["llm-models"])

LLM_MODEL_LABELS: dict[LLMModel, str] = {
    LLMModel.GEMINI_PRO: "Gemini 3 Pro",
    LLMModel.GEMINI_31_PRO: "Gemini 3.1 Pro",
    LLMModel.GEMINI_FLASH: "Gemini 3 Flash",
    LLMModel.VERTEX_AI: "Vertex AI Endpoint",
    LLMModel.VERTEX_MG_LLAMA: "Vertex MG — Llama",
    LLMModel.VERTEX_MG_MISTRAL: "Vertex MG — Mistral",
    LLMModel.VERTEX_MG_GEMMA: "Vertex MG — Gemma",
    LLMModel.VERTEX_MG_GLM: "Vertex MG — GLM",
    LLMModel.GPT_OSS_20B: "GPT OSS 20B",
    LLMModel.GPT_OSS_120B: "GPT OSS 120B",
    LLMModel.GLM_5_FP8: "GLM 5 FP8",
    LLMModel.DEEPSEEK_V3_2: "DeepSeek V3.2",
    LLMModel.GEMMA_3_27B: "Gemma 3 27B",
    LLMModel.GEMMA_3_12B: "Gemma 3 12B",
    LLMModel.GLM_5_MAAS: "GLM 5 MaaS (Global)",
    LLMModel.QWEN_2_5_72B: "Qwen 2.5 72B",
    LLMModel.QWEN_3_5: "Qwen 3.5",
    LLMModel.KIMI_K2_5: "Kimi K2.5",
}


class LLMModelOption(BaseModel):
    value: str
    label: str


@router.get("/llm-models", response_model=list[LLMModelOption])
async def list_llm_models() -> list[LLMModelOption]:
    """List all supported LLM models."""
    return [
        LLMModelOption(value=m.value, label=LLM_MODEL_LABELS.get(m, m.name))
        for m in LLMModel
    ]
