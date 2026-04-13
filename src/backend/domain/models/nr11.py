from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class NR11Data(BaseModel):
    """Structured data extracted from NR-11 training certificates."""

    model_config = {
        "extra": "ignore"
    }

    nome: str = Field(
        default=None,
        description="Full name of the holder, exactly as printed on the document.",
    )

    cpf: str = Field(
        default=None,
         description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX). Return empty string if not visible.",
    )

    nome_treinamento: str = Field(
        default=None,
        description="Name of the NR-11 training course completed (e.g., 'Caminhão Guindauto NR-11'), exactly as written.",
    )

    carga_horaria: str = Field(
        default=None,
        description="Training workload duration in the format 'x horas' (e.g., '24 horas').",
    )

    data: date = Field(
        default=None,
        description="Signature date or document date in ISO 8601 format (YYYY-MM-DD). Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )

    assinado: bool = Field(
        default=None,
        description="Indicates whether the document is signed.",
    )