from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class OperadorTreinamentoData(BaseModel):
    """Structured data extracted from operator training documents."""

    nome: str = Field(
        default=None,
        description="Full name of the operator exactly as printed on the document.",
    )

    cpf: str = Field(
        default=None,
        description="Brazilian CPF number of the operator, including punctuation if present (e.g., 000.000.000-00).",
    )

    rg: Optional[str] = Field(
        default=None,
        description="Brazilian RG number if present. Return null if not available.",
    )

    treinamento: str = Field(
        default=None,
        description="Name of the training or certification completed by the operator, exactly as written.",
    )

    carga_horaria: str = Field(
        default=None,
        description="Training workload duration in the format 'x horas' (e.g., '24 horas').",
    )

    data: date = Field(
        default=None,
        description="Expiration or validity date of the document in ISO 8601 format (YYYY-MM-DD).",
    )

    assinado: bool = Field(
        default=None,
        description="Indicates whether the document contains a visible signature (true if signed, false otherwise).",
    )