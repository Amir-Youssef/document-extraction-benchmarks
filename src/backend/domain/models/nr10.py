from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class NR10Data(BaseModel):
    """Structured data extracted from a NR-10 training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description = "Full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX)." \
        " Return empty string if not visible.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Training completion date in ISO 8601 format (YYYY-MM-DD). "
        "Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )