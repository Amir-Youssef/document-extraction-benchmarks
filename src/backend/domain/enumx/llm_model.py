from enum import Enum


class LLMModel(str, Enum):
    """Supported LLM models for document extraction.

    To add a new model, simply add a new enum member here and register
    its builder in ``infra.llm.model_factory.MODEL_REGISTRY``.
    """

    GEMINI_31_PRO = "gemini-31-pro"
    GEMINI_FLASH = "gemini-flash"
    VERTEX_AI = "vertex-ai"
    GEMMA_3_27B = "gemma-3-27b"
    GEMMA_3_12B = "gemma-3-12b"
    KIMI_K2_5 = "kimi-k2-5"
    QWEN3_VL = "qwen3-vl"
    QWEN_3_5_27B = "qwen-3-5-27b"
    QWEN_3_5_35B = "qwen-3-5-35b"
    QWEN_3_5_9B = "qwen-3-5-9b"
    OLLAMA_GEMMA_3_12B = "ollama-gemma-3-12b"
    OLLAMA_GEMMA_3_27B = "ollama-gemma-3-27b"
    OLLAMA_QWEN3_VL = "ollama-qwen3-vl"
    OLLAMA_QWEN3_VL_30B = "ollama-qwen3-vl-30b"
