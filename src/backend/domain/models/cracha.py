from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class CrachaData(BaseModel):
    """Structured data extracted from an operator badge (crachá de operador)."""

    nome: Optional[str] = Field(
        default=None,
        description="Full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the holder in Brazilian format (XXX.XXX.XXX-XX)."
        " Return null if not visible.",
    )

    rg: Optional[str] = Field(
        default=None,
        description="RG (identity document) number of the holder exactly as printed."
        " Return null if not visible.",
    )

    treinamento: Optional[str] = Field(
        default=None,
        description="Name of the training exactly as printed on the badge.",
    )

    carga_horaria: Optional[str] = Field(
        default=None,
        description="Training workload duration in the format 'x horas' (e.g., '24 horas').",
    )

    data: Optional[date] = Field(
        default=None,
        description="Date shown on the badge in ISO 8601 format (YYYY-MM-DD). "
        "Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )

    assinado: Optional[bool] = Field(
        default=None,
        description="Whether the badge contains a visible signature (true/false).",
    )
