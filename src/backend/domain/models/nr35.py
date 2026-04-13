from typing import Optional
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class NR35Data(BaseModel):
    """Structured data extracted from a NR-35 training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description ="the full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).",
    )

    treinamento: Optional[str] = Field(
        default=None,
        description="name of the training exactly as printed in the document.",
    )

    data: Optional[date] = Field(
        default=None,
        description="training date in YYYY-MM-DD format.",
    )

    carga_horaria: Optional[str] = Field(
        default=None,
        description="duration as written only this format (e.g. '24 horas' '8 horas' '10 horas')",
    )
