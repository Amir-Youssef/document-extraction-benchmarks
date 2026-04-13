from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class MarinheiroData(BaseModel):
    """Structured data extracted from a Brazilian Seafarer (Marinheiro) license."""

    nome: Optional[str] = Field(
        default=None,
        description="Full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX). " \
        "Return empty string if not visible.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Expiration date of the CNH in ISO 8601 format (YYYY-MM-DD). "
        "Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )