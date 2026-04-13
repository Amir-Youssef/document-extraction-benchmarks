from enum import Enum


class DocumentType(str, Enum):
    """Supported document types for extraction."""

    CNH = "cnh"
    ASO = "aso"
    CERTIFICATE = "certificate"
    EPI = "epi"
    FICHA_REGISTRO = "ficha_registro"
    LTCAT = "ltcat"
    NR12 = "nr12"
    PGR = "pgr"
    PCMSO = "pcmso"
    AFOGADOS = "afogados"
    ARRAIS = "arrais"
    NR35 = "nr35"
    MARINHEIRO = "marinheiro"
    NR10 = "nr10"
    NR10SEP = "nr10sep"
    SEGURO = "seguro"
    NR5 = "nr5"
    OPERADOR_TREINAMENTO = "operador_treinamento"
    NR11 = "nr11"
    NR33 = "nr33"
    ESCAVADEIRA = "escavadeira"
