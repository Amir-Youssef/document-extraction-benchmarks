from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from backend.core.config import MODEL_IDENTIFIERS, Settings
from backend.domain.enumx.llm_model import LLMModel


class ModelFactory:
    """Builds pydantic-ai Model instances from ``LLMModel`` enum members.

    To support a new provider (e.g. OpenAI, Anthropic), add a private
    builder method and register it in ``_BUILDERS``.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[LLMModel, Model] = {}
        self._BUILDERS: dict[LLMModel, callable] = {  # type: ignore[type-arg]
            LLMModel.GEMINI_31_PRO: self._build_gemini,
            LLMModel.GEMINI_FLASH: self._build_gemini,
        }

    def build(self, llm_model: LLMModel) -> Model:
        """Return a pydantic-ai ``Model`` for the requested enum member.

        Cached: the same ``LLMModel`` always returns the same instance.

        Args:
            llm_model: The model variant to instantiate.

        Raises:
            ValueError: If no builder is registered for the model.
        """
        cached = self._cache.get(llm_model)
        if cached is not None:
            return cached

        builder = self._BUILDERS.get(llm_model)
        if builder is None:
            raise ValueError(
                f"No builder registered for model: {llm_model.value!r}"
            )
        model = builder(llm_model)
        self._cache[llm_model] = model
        return model

    # ── Provider builders ────────────────────────────────────────────

    def _build_gemini(self, llm_model: LLMModel) -> GoogleModel:
        """Build a Google Gemini model via pydantic-ai."""
        api_key = self._settings.gemini_api_key or None
        provider = GoogleProvider(api_key=api_key)
        model_id = MODEL_IDENTIFIERS[llm_model]
        return GoogleModel(model_id, provider=provider)
