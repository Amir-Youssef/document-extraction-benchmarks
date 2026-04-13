"""vLLM / OpenAI-compatible multimodal client.

Converts PDFs to images and sends them via the standard OpenAI
chat completions API format, using static Bearer token authentication.
"""

import base64
import json
import logging
import re

import httpx
from pydantic import BaseModel

from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm.parsed_dates import normalize_parsed_dict_dates
from backend.infra.llm.vertex_gemma_client import _pdf_to_png

logger = logging.getLogger(__name__)


class VLLMClient(LLMClient):
    """LLMClient for vLLM endpoints with multimodal support."""

    def __init__(
        self,
        *,
        url: str,
        api_key: str,
        model_name: str,
    ) -> None:
        self._url = url
        self._api_key = api_key
        self._model_name = model_name

        logger.info(
            "Using vLLM multimodal client\nModel: %s\nURL: %s",
            self._model_name,
            self._url,
        )

    @staticmethod
    def _schema_to_simple_spec(output_model: type[BaseModel]) -> str:
        """Reuse the same prompt format as Gemma/Kimi."""
        from backend.infra.llm.vertex_gemma_client import VertexGemmaClient
        return VertexGemmaClient._schema_to_simple_spec(output_model)

    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        field_spec = self._schema_to_simple_spec(output_model)
        mime_type = self._detect_mime_type(content)

        if mime_type == "application/pdf":
            image_bytes = _pdf_to_png(content)
            image_mime = "image/png"
        else:
            image_bytes = content
            image_mime = mime_type

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

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        # JSON Schema do modelo Pydantic para guided decoding
        schema = output_model.model_json_schema()

        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime};base64,{image_b64}",
                            },
                        },
                    ],
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": output_model.__name__,
                    "schema": schema,
                },
            },
            "temperature": 0.1,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(self._url, json=payload, headers=headers)
            if not resp.is_success:
                raise RuntimeError(f"vLLM HTTP {resp.status_code}: {resp.text}")

        result = resp.json()
        raw_text = result["choices"][0]["message"]["content"]

        logger.info("vLLM raw response (first 500 chars): %s", (raw_text or "")[:500])

        parsed = self._extract_json(raw_text)
        parsed = {k: (None if v == "" else v) for k, v in parsed.items()}
        parsed = normalize_parsed_dict_dates(parsed, output_model)
        return output_model.model_validate(parsed)

    @staticmethod
    def _extract_json(text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from response: {text[:500]}")

    @staticmethod
    def _detect_mime_type(content: bytes) -> str:
        if content[:5] == b"%PDF-":
            return "application/pdf"
        if content[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if content[:2] == b"\xff\xd8":
            return "image/jpeg"
        return "application/octet-stream"
