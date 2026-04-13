"""Vertex AI Gemma multimodal client.

Converts PDFs to images and sends them via the OpenAI-compatible
chat completions API exposed by vLLM on Vertex AI endpoints,
using direct HTTP calls with shared token caching.
"""

import base64
import json
import logging
import re

import fitz  # PyMuPDF
import httpx
from pydantic import BaseModel

from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import LLMClient
from backend.infra.llm._token_cache import auth_headers
from backend.infra.llm.parsed_dates import normalize_parsed_dict_dates

logger = logging.getLogger(__name__)


def _pdf_to_png(pdf_bytes: bytes, dpi: int = 200) -> bytes:
    """Convert the first page of a PDF to a PNG image."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


def _build_endpoint_url(
    project_id: str, location: str, endpoint_id: str,
    dedicated_domain: str = "",
) -> str:
    """Build the endpoint URL.

    - Dedicated domain → ``:predict`` (Vertex wraps via ``@requestFormat``)
    - Shared domain   → ``/chat/completions`` (vLLM native OpenAI format)
    """
    if dedicated_domain:
        return (
            f"https://{dedicated_domain}/v1/projects/{project_id}"
            f"/locations/{location}/endpoints/{endpoint_id}:predict"
        )
    if location == "global":
        base = "aiplatform.googleapis.com"
    else:
        base = f"{location}-aiplatform.googleapis.com"
    return (
        f"https://{base}/v1/projects/{project_id}"
        f"/locations/{location}/endpoints/{endpoint_id}/chat/completions"
    )


class VertexGemmaClient(LLMClient):
    """LLMClient for Gemma 3 on Vertex AI with multimodal support.

    Converts PDFs to images and sends them via the vLLM
    OpenAI-compatible chat completions format through direct HTTP,
    replacing the previous google.cloud.aiplatform SDK.
    """

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        endpoint_id: str,
        model_name: str,
        dedicated_domain: str = "",
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._endpoint_id = endpoint_id
        self._model_name = model_name
        self._dedicated = bool(dedicated_domain)
        self._url = _build_endpoint_url(
            project_id, location, endpoint_id, dedicated_domain
        )

        mode = ":predict (dedicated)" if self._dedicated else "chat/completions (shared)"
        logger.info(
            "Using Vertex Gemma multimodal (HTTP) [%s]\nModel: %s\nEndpoint: %s\nLocation: %s\nURL: %s",
            mode,
            self._model_name,
            self._endpoint_id,
            self._location,
            self._url,
        )

    @staticmethod
    def _schema_to_simple_spec(output_model: type[BaseModel]) -> str:
        """Convert a Pydantic model into a simple field spec that Gemma understands.

        Instead of the full JSON Schema (which Gemma echoes back), produces
        a flat example like:
          {"nome": "string - Full name", "cpf": "string - CPF number", ...}
        """
        fields = output_model.model_fields
        example: dict[str, str] = {}
        for name, field_info in fields.items():
            # Determine type label
            annotation = field_info.annotation
            type_label = "string"
            origin = getattr(annotation, "__origin__", None)
            if origin is not None:
                # Optional[X] → get inner type
                args = getattr(annotation, "__args__", ())
                inner = next((a for a in args if a is not type(None)), None)
                if inner is not None:
                    annotation = inner
            if annotation in (int, float):
                type_label = annotation.__name__
            elif annotation is bool:
                type_label = "boolean"

            desc = field_info.description or ""
            example[name] = f"{type_label} - {desc}" if desc else type_label
        return json.dumps(example, indent=2, ensure_ascii=False)

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

        # Convert PDF to image for multimodal processing
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

        # Build messages (OpenAI chat format)
        messages = [
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
        ]

        if self._dedicated:
            # Dedicated endpoint: :predict with @requestFormat wrapper
            chat_request = {
                "@requestFormat": "chatCompletions",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
            payload = {"instances": [chat_request]}
        else:
            # Shared endpoint: raw OpenAI chat completions
            payload = {
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.1,
            }

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                self._url, json=payload, headers=auth_headers()
            )
            if not resp.is_success:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

        result = resp.json()

        # Parse response based on endpoint mode
        if self._dedicated:
            # :predict response: {"predictions": {"choices": [...]}}
            preds = result.get("predictions", {})
            if isinstance(preds, dict) and "choices" in preds:
                raw_text = preds["choices"][0]["message"].get("content", "")
            elif isinstance(preds, list) and preds and isinstance(preds[0], dict) and "choices" in preds[0]:
                raw_text = preds[0]["choices"][0]["message"].get("content", "")
            elif isinstance(preds, list):
                raw_text = self._parse_prediction(preds)
            else:
                raw_text = str(preds)
        elif "choices" in result:
            raw_text = result["choices"][0]["message"]["content"]
        elif "predictions" in result:
            raw_text = self._parse_prediction(result["predictions"])
        else:
            raw_text = resp.text

        logger.info("Gemma raw response (first 500 chars): %s", (raw_text or "")[:500])

        parsed = self._extract_json(raw_text)

        # Gemma sometimes returns the JSON Schema structure instead of
        # a flat object — the actual values end up inside "properties".
        if "properties" in parsed and isinstance(parsed["properties"], dict):
            has_schema_keys = {"title", "type", "description"} & parsed.keys()
            if has_schema_keys:
                props = parsed["properties"]
                # If the values are still schema dicts (e.g. {"anyOf":..., "title":...}),
                # try to extract a "default" or give up and use None.
                flat: dict[str, object] = {}
                for k, v in props.items():
                    if isinstance(v, dict) and ("anyOf" in v or "type" in v):
                        flat[k] = v.get("default")
                    else:
                        flat[k] = v
                parsed = flat

        parsed = {k: (None if v == "" else v) for k, v in parsed.items()}
        parsed = normalize_parsed_dict_dates(parsed, output_model)
        return output_model.model_validate(parsed)

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
            f"Could not extract valid JSON from Gemma response: {text[:500]}"
        )

    @staticmethod
    def _detect_mime_type(content: bytes) -> str:
        if content[:5] == b"%PDF-":
            return "application/pdf"
        if content[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if content[:2] == b"\xff\xd8":
            return "image/jpeg"
        if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"
        return "application/octet-stream"
