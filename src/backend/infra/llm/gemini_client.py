from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent

from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm.model_factory import ModelFactory


class PydanticAILLMClient(LLMClient):
    """Provider-agnostic LLMClient powered by pydantic-ai.

    The concrete model (Gemini Pro, Flash, etc.) is resolved at
    call-time via ``ModelFactory``, so adding a new model only
    requires updating the enum + factory registry.
    """

    def __init__(self, model_factory: ModelFactory, default_model: LLMModel) -> None:
        self._model_factory = model_factory
        self._default_model = default_model

    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        """Send document bytes to the chosen LLM and return validated structured output."""
        chosen = llm_model or self._default_model
        model = self._model_factory.build(chosen)
        mime_type = self._detect_mime_type(content)

        agent = Agent(
            model=model,
            output_type=output_model,
            system_prompt=system_prompt,
        )

        result = await agent.run(
            user_prompt=[BinaryContent(data=content, media_type=mime_type)],  # type: ignore
        )
        return result.output

    @staticmethod
    def _detect_mime_type(content: bytes) -> str:
        """Infer MIME type from file magic bytes."""
        if content[:5] == b"%PDF-":
            return "application/pdf"

        if content[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"

        if content[:2] == b"\xff\xd8":
            return "image/jpeg"

        if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"

        return "application/octet-stream"
