from datetime import date

from pydantic import BaseModel, Field


class FichaRegistroData(BaseModel):
    """Structured data extracted from a Brazilian Employee Registration Form (Ficha de Registro)."""

    nome_empregado: str = Field(
        description="Full name of the employee exactly as printed on the document.",
    )

    nome_empregador: str = Field(
        description="Legal name of the employer or company as written on the document.",
    )

    cpf_empregado: str = Field(
        description="CPF number of the employee (numbers only or formatted as XXX.XXX.XXX-XX).",
    )

    cargo: str = Field(
        description="Job title or position of the employee exactly as printed.",
    )

    data: date = Field(
        description="Employee hiring/admission date converted to ISO 8601 format (YYYY-MM-DD). Extract from DD/MM/YYYY format.",
    )