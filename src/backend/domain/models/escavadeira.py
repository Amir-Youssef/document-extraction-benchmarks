from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EscavadeiraData(BaseModel):
    """Structured data extracted from a hydraulic excavator operator training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description="Full name of the certificate holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the certificate holder in Brazilian format (XXX.XXX.XXX-XX)."
        " Return null if not visible.",
    )

    curso: Optional[str] = Field(
        default=None,
        description="Full name of the training course exactly as printed on the document.",
    )

    data: Optional[str] = Field(
    default=None,
    description="Training completion date in YYYY-MM-DD format. Do NOT use the expiration date.",
)

    carga_horaria: Optional[str] = Field(
        default=None,
        description="Training workload duration in the only format 'x horas' (e.g., '24 horas').",
    )

    empresa: Optional[str] = Field(
        default=None,
        description="Name of the institution that issued the certificate, exactly as printed.",
    )