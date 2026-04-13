from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EPIData(BaseModel):
    """Structured data extracted from an EPI (Ficha de Entrega de EPI)."""

    nome: Optional[str] = Field(
        default=None,
        description="Full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX). Return empty string if not visible.",
    )

    funcao: Optional[str] = Field(
        default=None,
        description="Job title or function of the employee as written on the document.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Signature date or document date in ISO 8601 format (YYYY-MM-DD). Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )


    assinado: Optional[bool] = Field(
        default=None,
        description="Indicates whether the document is signed.",
    )
