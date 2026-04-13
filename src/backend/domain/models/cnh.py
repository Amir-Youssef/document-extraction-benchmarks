from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class CNHData(BaseModel):
    """Structured data extracted from a Brazilian CNH (driver's license)."""

    nome: Optional[str] = Field(
        default=None,
        description = "the full name of the holder, exactly as printed on the document.",
    )

    numero_registro: Optional[str] = Field(
        default=None,
        description="the registration number exactly as printed on the document.",
    )

    cpf: Optional[str] = Field(
        default=None,
        description="CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).",
    )

    data: Optional[date] = Field(
        default=None,
        description="Expiration date of the CNH in ISO 8601 format (YYYY-MM-DD). \
        Convert from formats like DD/MM/YYYY or DD/MM/YY.",
    ) 

    categoria: Optional[str] = Field(
        default=None,
        description="the driver's license category. You MUST locate and extract this field.\n"
    )

