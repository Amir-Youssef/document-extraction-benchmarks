from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class NR33Data(BaseModel):
    """Structured data extracted from a NR-33 training certificate."""

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
    description="Signature date or document date in ISO 8601 format (YYYY-MM-DD).",
   )

    carga_horaria: Optional[str] = Field(
        default=None,
        description="duration as written only this format (e.g. '24 horas' '8 horas' '10 horas')",
    )

    empresa: Optional[str] = Field(
        default=None,
        description="Name of the institution that issued the certificate, exactly as printed.",
    )