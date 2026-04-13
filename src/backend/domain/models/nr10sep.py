from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class NR10SEPData(BaseModel):
    """Structured data extracted from a NR-10 SEP training certificate."""

    nome: Optional[str] = Field(
        default=None,
        description = "Full name of the holder, exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF or CNPJ number of the holder in Brazilian format (CPF: XXX.XXX.XXX-XX or CNPJ: XX.XXX.XXX/XXXX-XX). " \
        "Return empty string if not visible.",
    )

    data: Optional[date] = Field(
        default=None,
        description="Training completion date in ISO 8601 format (YYYY-MM-DD). "
        "Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    )