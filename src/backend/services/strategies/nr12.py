from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.nr12 import NR12Data


class NR12ExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for NR12 training certificates."""

    document_type: DocumentType = DocumentType.NR12

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian occupational safety training certificates.\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- nome: full name of the trained worker exactly as written on the document\n"
        "- cpf: CPF number of the trained worker\n"
        "- treinamento: name of the training exactly as printed\n"
        "- empresa: legal name of the company associated with the worker or training\n"
        "- data: signature date or main document date\n"
        "- carga_horaria: training workload duration in the format 'x horas' (e.g., '4 horas', '8 horas').\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- 'nome' must correspond to the trained worker receiving the certificate, not instructors or signatories.\n"
        "- CPF must follow the Brazilian format XXX.XXX.XXX-XX if present.\n"
        "- If CPF appears only as digits, format it to XXX.XXX.XXX-XX.\n"
        "- 'treinamento' should correspond to the NR12 training name shown on the certificate.\n"
        "- 'empresa' should correspond to the company associated with the worker or the training certificate.\n"
        "- 'carga_horaria' must be extracted exactly as written in the document.\n"
        "- Convert any Brazilian date formats (e.g., DD/MM/YYYY or DD/MM/YY) to ISO 8601 format (YYYY-MM-DD).\n"
        "- If multiple dates appear, prioritize the certificate issue date or signature date.\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> NR12Data:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NR12Data,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore