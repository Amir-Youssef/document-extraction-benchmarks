from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ASOData(BaseModel):
    """Structured data extracted from a ASO."""

    nome: Optional[str] = Field(
        default=None,
        description = "the full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).",
    )

    apto: Optional[str] = Field(
        default=None,
        description="whether the worker is declared fit or unfit for the position, return only 'APTO' or 'INAPTO'.",
    )

    data: Optional[date] = Field(
        default=None,
        description="document signature date in YYYY-MM-DD format (ISO 8601).",
    )

    funcao: Optional[str] = Field(
        default=None,
        description="the job title or function of the employee exactly as printed in the document, only the function name without digits.",
    )

