from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PGRData(BaseModel):
    """Structured data extracted from a Brazilian PGR document."""

    empresa: str = Field(
        description="Legal name of the company exactly as written in the document.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Date when the document expires or loses its validity, in ISO 8601 format (YYYY-MM-DD).",
    )

    autor: str = Field(
        description="Name of the responsible technical professional exactly as printed.",
    )