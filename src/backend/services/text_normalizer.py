"""Normalize confusable Unicode characters in extracted text fields."""

import unicodedata

from pydantic import BaseModel

_REPLACEMENTS: dict[str, str] = {
    "\u2013": "-",    # en dash → hyphen
    "\u2014": "-",    # em dash → hyphen
    "\u2018": "'",    # left single smart quote → apostrophe
    "\u2019": "'",    # right single smart quote → apostrophe
    "\u201c": '"',    # left double smart quote → quotation mark
    "\u201d": '"',    # right double smart quote → quotation mark
    "\u00a0": " ",    # non-breaking space → space
    "\u2026": "...",  # horizontal ellipsis → three dots
}

_TRANS_TABLE = str.maketrans(_REPLACEMENTS)


def _strip_accents(value: str) -> str:
    """Remove diacritical marks (accents) from text."""
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _normalize_text(value: str) -> str:
    return _strip_accents(value.translate(_TRANS_TABLE))


def normalize_model(model: BaseModel) -> BaseModel:
    """Return a copy of *model* with confusable Unicode chars replaced in all str fields."""
    updates: dict[str, str] = {}
    for name, field_info in model.model_fields.items():
        value = getattr(model, name)
        if isinstance(value, str):
            normalized = _normalize_text(value)
            if normalized != value:
                updates[name] = normalized
    if not updates:
        return model
    return model.model_copy(update=updates)
