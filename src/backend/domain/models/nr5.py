from datetime import date
from pydantic import BaseModel, Field
from typing import Optional


class NR5Data(BaseModel):
    """Structured data extracted from a NR-5 training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description = "the full name of the holder, exactly as printed on the document.",
    )
    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).",
    )
    treinamento: Optional[str] = Field(
        default=None,
        description="name of the training exactly as printed in the document. Format ('training name')",
    )
    carga_horaria: Optional[str] = Field(
        default=None,
        description="total workload of the training exactly as printed in the document.",
    )
    data: Optional[date] = Field(
        default=None,
        description="training completion date in YYYY-MM-DD format.",
    )
