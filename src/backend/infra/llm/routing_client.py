"""Composite LLM client that routes calls to the correct backend.

When the chosen ``LLMModel`` belongs to ``VERTEX_MG_MODELS``, the
request is forwarded to the matching ``VertexAILLMClient``; all other
models are handled by the default (pydantic-ai) client.  This keeps
both adapters decoupled while presenting a single ``LLMClient`` to the
rest of the application.
"""

import logging

from pydantic import BaseModel

from backend.core.config import VERTEX_MG_MODELS
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient

logger = logging.getLogger(__name__)


class RoutingLLMClient(LLMClient):
    """Dispatches ``extract_structured`` to the appropriate backend client."""

    def __init__(
        self,
        *,
        default_client: LLMClient,
        vertex_clients: dict[LLMModel, LLMClient],
        default_model: LLMModel,
    ) -> None:
        self._default_client = default_client
        self._vertex_clients = vertex_clients
        self._default_model = default_model

    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        chosen = llm_model or self._default_model

        if chosen in VERTEX_MG_MODELS:
            vertex_client = self._vertex_clients.get(chosen)
            if vertex_client is not None:
                return await vertex_client.extract_structured(
                    content=content,
                    output_model=output_model,
                    system_prompt=system_prompt,
                    llm_model=chosen,
                )
            raise ValueError(
                f"No Vertex AI client configured for model {chosen.value!r}. "
                f"Set the corresponding endpoint ID in the .env file."
            )

        return await self._default_client.extract_structured(
            content=content,
            output_model=output_model,
            system_prompt=system_prompt,
            llm_model=chosen,
        )
