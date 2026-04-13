from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class SeguroData(BaseModel):
    """Structured data extracted from an insurance policy document."""

    nome: Optional[str] = Field(
        default=None,
        description = "Full name of the holder or company, exactly as printed on the document.",
    )

    documento: Optional[str] = Field(
        default=None,
        description="CPF or CNPJ number of the holder. CPF must be in Brazilian format (XXX.XXX.XXX-XX) "
        "and CNPJ must be in Brazilian format (XX.XXX.XXX/XXXX-XX). "
    )

    data: Optional[date] = Field(
        default=None,
        description="Policy expiration date in ISO 8601 format (YYYY-MM-DD). "
        "Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )