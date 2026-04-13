from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.afogados import AfogadosData


class AfogadosExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for drowning rescue training certificates."""

    document_type: DocumentType = DocumentType.AFOGADOS

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian documents.\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- nome: full name of the certificate holder, exactly as written on the document\n"
        "- cpf: CPF number of the certificate holder\n"
        "- data: date of the training or main document date\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- The 'nome' must correspond to the person receiving the certificate, not instructors or signatories.\n"
        "- CPF must follow the Brazilian format XXX.XXX.XXX-XX if present.\n"
        "- Convert any Brazilian date formats (e.g., DD/MM/YYYY or DD/MM/YY) to ISO 8601 format (YYYY-MM-DD).\n"
        "- If multiple dates appear, prioritize the training date or the main certificate date.\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> AfogadosData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=AfogadosData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore
