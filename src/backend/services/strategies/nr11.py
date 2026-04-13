from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.nr11 import NR11Data


class NR11ExtractionStrategy(DocumentExtractionStrategy):
    """Strategy for extracting NR-11 training certificates."""

    document_type: DocumentType = DocumentType.NR11

    SYSTEM_PROMPT: str = (
        "You are a specialist in Brazilian NR-11 occupational safety training certificates.\n\n"
        "Return ONLY raw JSON. No markdown, no explanation.\n\n"
        "Extract:\n"
        "- nome: full name exactly as printed\n"
        "- cpf: exactly as printed, with punctuation (format XXX.XXX.XXX-XX)\n"
        "- nome_treinamento: equipment name and NR number exactly as written\n"
        "- carga_horaria: duration as written (e.g. '24 horas')\n"
        "- data: certificate issue date in YYYY-MM-DD\n"
        "- assinado: true / false / null\n\n"
        "NOME_TREINAMENTO RULES:\n"
        "- Copy only the course title — do NOT include surrounding phrases\n"
        "- WRONG: 'Treinamento de Operador de Escavadeira Hidraulica' → RIGHT: 'Escavadeira Hidraulica'\n"
        "- WRONG: 'Caminhão Guindauto NR-11,' → RIGHT: 'Caminhão Guindauto NR-11'\n"
        "- Remove any trailing punctuation (commas, periods, semicolons)\n"
        "- Do NOT normalize NR format: 'NR-11', 'NR11', 'Nr11' are all valid as written\n\n"
        "EXAMPLE:\n"
        "{\n"
        '  "nome": "Carlos Ivanio Lima Bortoletti",\n'
        '  "cpf": "084.406.849-75",\n'
        '  "nome_treinamento": "Caminhão Guindauto NR-11",\n'
        '  "carga_horaria": "24 horas",\n'
        '  "data": "2024-09-08",\n'
        '  "assinado": true\n'
        "}\n\n"
        "Missing fields → null\n"
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> NR11Data:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NR11Data,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore