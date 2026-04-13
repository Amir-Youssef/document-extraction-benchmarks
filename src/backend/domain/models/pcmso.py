from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class PCMSOData(BaseModel):
    """Structured data extracted from a Brazilian PCMSO document."""

    nome_empresa: Optional[str] = Field(
        default=None,
        description="Legal company name exactly as written.",
    )

    cnpj: Optional[str] = Field(
        default=None,
        description="CNPJ of the company, numbers only if available.",
    )

    responsavel_empresa: Optional[str] = Field(
        default=None,
        description="Name of the responsible company representative exactly as printed.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Date when the document expires or loses its validity, in ISO 8601 format (YYYY-MM-DD).",
    )

    assinado: Optional[bool] = Field(
        default=None,
        description="Indicates whether the document is signed.",
    )