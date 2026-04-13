"""Ollama LLM client.

Sends documents to a self-hosted Ollama instance via the ``/api/chat``
endpoint. Vision-capable models receive PDFs converted to PNG images.
"""

import base64
import logging

import httpx
from pydantic import BaseModel

from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm.parsed_dates import normalize_parsed_dict_dates
from backend.infra.llm.vertex_gemma_client import (
    _pdf_to_png,
    VertexGemmaClient,
)

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """LLMClient for multimodal models served by an Ollama instance."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        model: str = "gemma3:12b",
        llm_model: LLMModel | None = None,
    ) -> None:
        base = base_url.rstrip("/")
        self._base_url = base
        self._api_key = api_key
        self._model = model
        self._llm_model = llm_model
        self._url = f"{base}/chat" if base.endswith("/api") else f"{base}/api/chat"

        logger.info(
            "Using Ollama client (Multimodal)\nModel: %s\nURL: %s",
            self._model,
            self._url,
        )

    def _request_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        key = (self._api_key or "").strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
            headers["X-API-Key"] = key
        return headers

    def _build_payload(
        self,
        *,
        content: bytes,
        mime_type: str,
        field_spec: str,
        system_prompt: str,
        output_model: type[BaseModel],
    ) -> dict:
        """Build Ollama /api/chat payload with a base64 image."""
        if mime_type == "application/pdf":
            image_bytes = _pdf_to_png(content)
        else:
            image_bytes = content

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        text_prompt = (
            f"Extract data from the document image and return ONLY a JSON object "
            f"with these fields (replace the descriptions with actual values):\n"
            f"{field_spec}\n\n"
            f"Rules:\n"
            f"- Return ONLY the JSON object, no other text.\n"
            f"- Use the extracted values, NOT the field descriptions.\n"
            f"- If a field is not visible, use null.\n"
        )

        return {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": text_prompt,
                    "images": [image_b64],
                },
            ],
            "stream": False,
            "format": output_model.model_json_schema(),
            "options": {"temperature": 0.1},
        }

    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        if "ollama.com" in self._base_url.lower() and not (self._api_key or "").strip():
            raise RuntimeError("Ollama Cloud requires API key.")

        field_spec = VertexGemmaClient._schema_to_simple_spec(output_model)
        mime_type = VertexGemmaClient._detect_mime_type(content)

        payload = self._build_payload(
            content=content, mime_type=mime_type,
            field_spec=field_spec, system_prompt=system_prompt,
            output_model=output_model,
        )

        headers = self._request_headers()

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(self._url, json=payload, headers=headers)
            if not resp.is_success:
                raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text}")

        result = resp.json()
        raw_text = result.get("message", {}).get("content", "")

        logger.info("Ollama raw response (first 500 chars): %s", (raw_text or "")[:500])

        parsed = VertexGemmaClient._extract_json(raw_text)
        parsed = {k: (None if v == "" else v) for k, v in parsed.items()}
        parsed = normalize_parsed_dict_dates(parsed, output_model)
        return output_model.model_validate(parsed)
