from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class NR12Data(BaseModel):
    """Structured data extracted from an NR12 training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description="Full name of the trained worker exactly as printed in the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX). Return empty string if not visible.",
    )

    treinamento: Optional[str] = Field(
        default=None,
        description="Name of the training exactly as printed in the document.",
    ) 

    empresa: Optional[str] = Field(
        default=None,
        description="Legal name of the company exactly as written in the document.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Signature date or document date in ISO 8601 format (YYYY-MM-DD). Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )

    carga_horaria: Optional[str] = Field(
        default=None,
        description="Training workload duration exactly as written (e.g., '4 horas', '8 horas').",
    )