"""Vertex AI endpoint LLM client.

Supports multimodal calling via Vertex AI native format (:predict) with
``instances``/``parameters``.

For PDF documents:
- Converts PDF to PNG via PyMuPDF and sends as ``image_url`` in
  OpenAI chat format wrapped in a Vertex instance.
"""

import base64
import json
import logging
import re

import httpx
from pydantic import BaseModel

from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm._token_cache import auth_headers
from backend.infra.llm.parsed_dates import normalize_parsed_dict_dates

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL builder
# ---------------------------------------------------------------------------

def _build_predict_url(
    project_id: str, location: str, endpoint_id: str,
) -> str:
    """Build the :predict URL for shared Vertex AI endpoints."""
    if location == "global":
        base = "aiplatform.googleapis.com"
    else:
        base = f"{location}-aiplatform.googleapis.com"
    return (
        f"https://{base}/v1/projects/{project_id}"
        f"/locations/{location}/endpoints/{endpoint_id}:predict"
    )


class VertexAILLMClient(LLMClient):
    """LLMClient implementation that calls a Vertex AI deployed endpoint.

    Uses ``:predict`` (Vertex native format) with multimodal support.
    Converts PDF to PNG via PyMuPDF before sending as an image object.
    """

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        endpoint_id: str,
        model_name: str,
        dedicated_domain: str = "",
        multimodal: bool = True,
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._endpoint_id = endpoint_id
        self._model_name = model_name
        self._dedicated_domain = dedicated_domain
        self._multimodal = multimodal

        if dedicated_domain:
            self._url = (
                f"https://{dedicated_domain}/v1/projects/{project_id}"
                f"/locations/{location}/endpoints/{endpoint_id}:predict"
            )
        else:
            self._url = _build_predict_url(
                project_id, location, endpoint_id
            )

        logger.info(
            "Using Vertex AI multimodal endpoint (HTTP)\nModel: %s\nEndpoint: %s\nLocation: %s\nURL: %s",
            self._model_name,
            self._endpoint_id,
            self._location,
            self._url,
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
        """Send document bytes to a Vertex AI endpoint and return structured output."""
        schema_json = json.dumps(output_model.model_json_schema(), indent=2)
        mime_type = self._detect_mime_type(content)

        # Multimodal: convert PDF->PNG
        if mime_type == "application/pdf":
            image_bytes = self._pdf_to_png(content)
            image_mime = "image/png"
        else:
            image_bytes = content
            image_mime = mime_type

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        text_prompt = (
            f"Return ONLY a valid JSON object matching this schema:\n"
            f"{schema_json}"
        )
        chat_request = {
            "@requestFormat": "chatCompletions",
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
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
        }
        payload = {"instances": [chat_request]}

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                self._url, json=payload, headers=auth_headers()
            )
            if not resp.is_success:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        preds = data.get("predictions", {})

        if isinstance(preds, dict) and "choices" in preds:
            msg = preds["choices"][0]["message"]
            raw_text = ""
            for field in ("content", "reasoning_content", "reasoning"):
                candidate = msg.get(field) or ""
                if "{" in candidate:
                    raw_text = candidate
                    break
            if not raw_text:
                raw_text = msg.get("content") or msg.get("reasoning_content") or ""
        elif isinstance(preds, list):
            raw_text = self._parse_prediction(preds)
        else:
            raw_text = str(preds)

        logger.debug("Raw model response (first 500 chars): %s", (raw_text or "")[:500])

        parsed = self._extract_json(raw_text)
        parsed = {k: (None if v == "" else v) for k, v in parsed.items()}
        parsed = normalize_parsed_dict_dates(parsed, output_model)
        return output_model.model_validate(parsed)

    # ── Response parsing ───────────────────

    @staticmethod
    def _parse_prediction(predictions: list) -> str:
        if not predictions:
            raise ValueError("Vertex AI endpoint returned no predictions")
        first = predictions[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            for key in ("text", "generated_text", "output", "content"):
                if key in first:
                    return str(first[key]).strip()
            return str(first)
        return str(first)

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

        raise ValueError(
            f"Could not extract valid JSON from Vertex AI response: {text[:500]}"
        )

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _pdf_to_png(pdf_bytes: bytes, dpi: int = 200) -> bytes:
        """Convert the first page of a PDF to a PNG image via PyMuPDF."""
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes

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
