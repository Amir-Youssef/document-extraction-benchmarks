"""Normaliza strings de data vindas do LLM antes da validação Pydantic."""

from __future__ import annotations

import re
from datetime import date, datetime
from types import UnionType
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

_YMD = re.compile(r"^(\d{4})[/.-](\d{2})[/.-](\d{2})$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_DMY_DOT = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        args = tuple(a for a in get_args(annotation) if a is not type(None))
        if len(args) == 1:
            return args[0]
    return annotation


def _is_date_field(annotation: Any) -> bool:
    ann = _unwrap_optional(annotation)
    return ann is date or ann is datetime


def _coerce_date_string(value: str) -> str:
    s = value.strip()
    if not s:
        return s
    m = _YMD.match(s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = _DMY_SLASH.match(s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"
    m = _DMY_DOT.match(s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"
    return s


_VALID_DATE = re.compile(r"\d{2,4}[/.\-]\d{2}[/.\-]\d{2,4}")


def normalize_parsed_dict_dates(
    parsed: dict[str, Any],
    output_model: type[BaseModel],
) -> dict[str, Any]:
    """Converte separadores (ex.: ``2024/01/29`` → ``2024-01-29``) em campos ``date``/``datetime``."""
    out = dict(parsed)
    for name, field in output_model.model_fields.items():
        if name not in out:
            continue
        if not _is_date_field(field.annotation):
            continue
        v = out[name]
        if isinstance(v, str):
            coerced = _coerce_date_string(v)
            if coerced and _VALID_DATE.match(coerced):
                out[name] = coerced
            else:
                out[name] = None
        elif v is not None and not isinstance(v, (date, datetime)):
            out[name] = None
    return out
