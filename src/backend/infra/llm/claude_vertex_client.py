"""Claude on Vertex AI LLM client.

Uses the Anthropic Messages API via Vertex AI's global endpoint
(``aiplatform.googleapis.com``) with Application Default Credentials.
"""

import base64
import json
import logging
import re

import httpx
from pydantic import BaseModel

from backend.core.config import MODEL_IDENTIFIERS
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm._token_cache import auth_headers
from backend.infra.llm.parsed_dates import normalize_parsed_dict_dates

logger = logging.getLogger(__name__)

_ANTHROPIC_VERSION = "vertex-2023-10-16"


class ClaudeVertexClient(LLMClient):
    """LLMClient implementation that calls Claude on Vertex AI.

    Uses the Anthropic Messages API format through the Vertex AI
    endpoint with shared token caching.
    """

    def __init__(
        self,
        *,
        project_id: str,
        location: str = "global",
    ) -> None:
        self._project_id = project_id
        self._location = location
        logger.info(
            "Configured Claude Vertex AI client — project=%s, location=%s",
            self._project_id,
            self._location,
        )

    # ── LLMClient contract ───────────────────────────────────────────

    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        """Send document content to Claude via Vertex AI and return structured output."""
        chosen = llm_model or LLMModel.VERTEX_MG_CLAUDE
        model_id = MODEL_IDENTIFIERS.get(chosen, "claude-sonnet-4-6")

        schema_json = json.dumps(output_model.model_json_schema(), indent=2)
        system_text = (
            f"{system_prompt}\n\n"
            f"Return ONLY a valid JSON object matching this schema:\n"
            f"{schema_json}"
        )

        mime_type = self._detect_mime_type(content)
        content_b64 = base64.b64encode(content).decode("utf-8")

        # Build Anthropic content blocks
        if mime_type == "application/pdf":
            doc_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": content_b64,
                },
            }
        else:
            doc_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": content_b64,
                },
            }

        request_body = {
            "anthropic_version": _ANTHROPIC_VERSION,
            "max_tokens": 4096,
            "temperature": 0.1,
            "system": system_text,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        doc_block,
                        {
                            "type": "text",
                            "text": "Extract all structured data from this document.",
                        },
                    ],
                }
            ],
        }

        if self._location == "global":
            base = "aiplatform.googleapis.com"
        else:
            base = f"{self._location}-aiplatform.googleapis.com"

        url = (
            f"https://{base}/v1/"
            f"projects/{self._project_id}/"
            f"locations/{self._location}/"
            f"publishers/anthropic/models/{model_id}:rawPredict"
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url, json=request_body, headers=auth_headers()
            )
            if not response.is_success:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
            response_json = response.json()

        logger.debug(
            "Claude Vertex response: %s",
            json.dumps(response_json, indent=2, ensure_ascii=False)[:2000],
        )

        raw_text = self._extract_raw_text(response_json)
        parsed = self._extract_json(raw_text.strip())
        parsed = normalize_parsed_dict_dates(parsed, output_model)
        return output_model.model_validate(parsed)

    # ── Response parsing ─────────────────────────────────────────────

    @staticmethod
    def _extract_raw_text(response_json: dict) -> str:
        """Extract text from Claude's Messages API response format."""
        if "error" in response_json:
            raise ValueError(
                f"Claude Vertex AI error: {str(response_json['error'])[:300]}"
            )

        content = response_json.get("content", [])
        if not content:
            raise ValueError(
                f"Claude Vertex AI returned empty content. "
                f"Response keys: {list(response_json.keys())}"
            )

        # Claude returns content blocks; find the first text block
        for block in content:
            if block.get("type") == "text":
                return block["text"]

        raise ValueError(
            f"No text block found in Claude response. "
            f"Block types: {[b.get('type') for b in content]}"
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract a JSON object from free-form model output."""
        # 1. Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Markdown code-block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. First '{' … last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not extract valid JSON from Claude response: {text[:300]}"
        )

    # ── Helpers ──────────────────────────────────────────────────────

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
