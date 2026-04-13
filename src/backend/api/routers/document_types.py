from fastapi import APIRouter
from pydantic import BaseModel

from backend.domain.enumx.document_type import DocumentType

router = APIRouter(prefix="/v1", tags=["document-types"])

DOCUMENT_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.CNH: "Carteira Nacional de Habilitação",
    DocumentType.ASO: "Atestado de Saúde Ocupacional",
    DocumentType.CERTIFICATE: "Certificado",
    DocumentType.EPI: "Ficha de EPI",
    DocumentType.FICHA_REGISTRO: "Ficha de Registro",
    DocumentType.LTCAT: "LTCAT",
    DocumentType.NR12: "NR12 - Treinamento",
    DocumentType.PGR: "PGR - Programa de Gerenciamento de Riscos",
    DocumentType.PCMSO: "PCMSO - Programa de Controle Médico de Saúde Ocupacional",
    DocumentType.AFOGADOS: "Certificado - Resgate de Afogamento",
    DocumentType.ARRAIS: "Licença de Arrais Amador",
    DocumentType.NR35: "NR35 - Certificado de treinamento",
    DocumentType.MARINHEIRO: "Carteira de Marinheiro",
    DocumentType.NR10: "NR10 - Certificado de treinamento",
    DocumentType.NR10SEP: "NR10 SEP - Certificado de treinamento",
    DocumentType.SEGURO: "Apólice de Seguro",
    DocumentType.NR5: "NR5 - Certificado de treinamento",
    DocumentType.OPERADOR_TREINAMENTO: "Carteirinha de Operador",
    DocumentType.NR11: "Treinamento NR-11",
    DocumentType.NR33: "NR33 - Certificado de treinamento",
    DocumentType.ESCAVADEIRA: "Certificado de Operador de Escavadeira Hidráulica",
}


class DocumentTypeOption(BaseModel):
    value: str
    label: str


@router.get("/document-types", response_model=list[DocumentTypeOption])
async def list_document_types() -> list[DocumentTypeOption]:
    """List all supported document types."""
    return [
        DocumentTypeOption(value=dt.value, label=DOCUMENT_TYPE_LABELS.get(dt, dt.name))
        for dt in DocumentType
    ]
