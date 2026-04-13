from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.core.config import MODEL_IDENTIFIERS, Settings, settings
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm.gemini_client import PydanticAILLMClient
from backend.infra.llm.model_factory import ModelFactory
from backend.infra.llm.routing_client import RoutingLLMClient
from backend.infra.llm.vertex_client import VertexAILLMClient
from backend.infra.llm.vertex_maas_client import VertexMaaSClient
from backend.infra.llm.vertex_gemma_client import VertexGemmaClient
from backend.services.factory import ExtractorFactory
from backend.services.orchestrator import DocumentOrchestrator


def get_settings() -> Settings:
    return settings


@lru_cache(maxsize=1)
def _cached_model_factory() -> ModelFactory:
    return ModelFactory(settings=settings)


@lru_cache(maxsize=1)
def _cached_pydantic_ai_client() -> PydanticAILLMClient:
    return PydanticAILLMClient(
        model_factory=_cached_model_factory(),
        default_model=settings.default_llm_model,
    )


# Deploy mode: (enum, endpoint_id attr, location attr, dedicated_domain attr)
_VERTEX_DEPLOY_MAP: list[tuple[LLMModel, str, str, str]] = [
    (LLMModel.VERTEX_AI,         "vertex_endpoint_id",             "",                      ""),
    (LLMModel.VERTEX_MG_LLAMA,   "vertex_mg_llama_endpoint_id",    "",                      ""),
    (LLMModel.VERTEX_MG_MISTRAL, "vertex_mg_mistral_endpoint_id",  "",                      ""),
    (LLMModel.VERTEX_MG_GEMMA,   "vertex_mg_gemma_endpoint_id",    "",                      ""),
    (LLMModel.VERTEX_MG_GLM,     "vertex_mg_glm_endpoint_id",      "",                      ""),
    (LLMModel.GPT_OSS_20B,       "gpt_oss_20b_endpoint_id",        "gpt_oss_20b_location",  ""),
    (LLMModel.GPT_OSS_120B,      "gpt_oss_120b_endpoint_id",       "gpt_oss_120b_location", ""),
    (LLMModel.GLM_5_FP8,         "glm_5_fp8_endpoint_id",          "glm_5_fp8_location",    ""),
    (LLMModel.DEEPSEEK_V3_2,     "deepseek_v3_2_endpoint_id",      "deepseek_v3_2_location",""),
    (LLMModel.QWEN_3_5,          "qwen_3_5_endpoint_id",           "qwen_3_5_location",     "qwen_3_5_dedicated_domain"),
]

# MaaS mode: (enum, settings attr model_name, settings attr region)
_VERTEX_MAAS_MAP: list[tuple[LLMModel, str, str]] = [
    (LLMModel.GLM_5_MAAS,    "glm_5_maas_model",    "glm_5_maas_region"),
    (LLMModel.QWEN_2_5_72B,  "qwen_2_5_72b_model",  "qwen_2_5_72b_region"),
]

# Gemma multimodal: (enum, settings attr endpoint_id, settings attr location, settings attr dedicated_domain)
_VERTEX_GEMMA_MAP: list[tuple[LLMModel, str, str, str]] = [
    (LLMModel.GEMMA_3_27B, "gemma_3_27b_endpoint_id", "gemma_3_27b_location", "gemma_3_27b_dedicated_domain"),
    (LLMModel.GEMMA_3_12B, "gemma_3_12b_endpoint_id", "gemma_3_12b_location", ""),
    (LLMModel.QWEN3_VL, "qwen3_vl_endpoint_id", "qwen3_vl_location", "qwen3_vl_dedicated_domain"),
    (LLMModel.KIMI_K2_5, "kimi_k2_5_endpoint_id", "kimi_k2_5_location", "kimi_k2_5_dedicated_domain"),
]


@lru_cache(maxsize=1)
def _cached_vertex_clients() -> dict[LLMModel, LLMClient]:
    """Create Vertex AI clients for every configured model.

    Supports 3 call modes following the erro.txt pattern:
    - Deploy (:predict) → VertexAILLMClient
    - MaaS (chat/completions) → VertexMaaSClient
    - Gemma multimodal (PDF→image) → VertexGemmaClient
    """
    if not settings.vertex_project_id:
        return {}

    clients: dict[LLMModel, LLMClient] = {}

    # 1. Deploy mode (:predict)
    for model, ep_attr, loc_attr, domain_attr in _VERTEX_DEPLOY_MAP:
        endpoint_id = getattr(settings, ep_attr, "")
        if not endpoint_id:
            continue
        loc_override = getattr(settings, loc_attr, "") if loc_attr else ""
        dedicated = getattr(settings, domain_attr, "") if domain_attr else ""
        clients[model] = VertexAILLMClient(
            project_id=settings.vertex_project_id,
            location=loc_override or settings.vertex_location,
            endpoint_id=endpoint_id,
            model_name=MODEL_IDENTIFIERS[model],
            dedicated_domain=dedicated,
        )

    # 2. MaaS mode (OpenAI chat completions)
    for model, model_attr, region_attr in _VERTEX_MAAS_MAP:
        model_name = getattr(settings, model_attr, "")
        if not model_name:
            continue
        region = getattr(settings, region_attr, "") or "global"
        clients[model] = VertexMaaSClient(
            project_id=settings.vertex_project_id,
            region=region,
            model_name=model_name,
        )

    # 3. Gemma multimodal (PDF → image via vLLM)
    for model, ep_attr, loc_attr, domain_attr in _VERTEX_GEMMA_MAP:
        endpoint_id = getattr(settings, ep_attr, "")
        if not endpoint_id:
            continue
        loc_override = getattr(settings, loc_attr, "")
        dedicated = getattr(settings, domain_attr, "") if domain_attr else ""
        clients[model] = VertexGemmaClient(
            project_id=settings.vertex_project_id,
            location=loc_override or settings.vertex_location,
            endpoint_id=endpoint_id,
            model_name=MODEL_IDENTIFIERS[model],
            dedicated_domain=dedicated,
        )

    return clients


@lru_cache(maxsize=1)
def _cached_llm_client() -> RoutingLLMClient:
    return RoutingLLMClient(
        default_client=_cached_pydantic_ai_client(),
        vertex_clients=_cached_vertex_clients(),
        default_model=settings.default_llm_model,
    )


def get_model_factory() -> ModelFactory:
    return _cached_model_factory()


def get_llm_client() -> LLMClient:
    return _cached_llm_client()


def get_factory(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> ExtractorFactory:
    return ExtractorFactory(llm_client=llm_client)


def get_orchestrator(
    factory: Annotated[ExtractorFactory, Depends(get_factory)],
) -> DocumentOrchestrator:
    return DocumentOrchestrator(factory=factory)
