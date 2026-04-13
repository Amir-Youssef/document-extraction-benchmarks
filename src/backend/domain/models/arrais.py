from typing import Optional
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ArraisData(BaseModel):
    """Structured data extracted from a Brazilian Arrais license."""

    
    nome: Optional[str] = Field(
        default=None,
        description = "the full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).",
    )

    data: Optional[date] = Field(
        default=None,
        description="date of validity of the document in YYYY-MM-DD format.",
    )

    numero_registro: Optional[str] = Field(
        default=None,
        description="registration number exactly as printed on the document.",
    )
