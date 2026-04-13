from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.pgr import PGRData


class PGRExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for Brazilian PGR (Programa de Gerenciamento de Riscos) documents."""

    document_type: DocumentType = DocumentType.PGR

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian occupational safety documents (PGR - Programa de Gerenciamento de Riscos).\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- empresa: legal name of the company for which the PGR was issued\n"
        "- data: date when the document expires or loses its validity\n"
        "- autor: name of the main technical responsible\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- 'empresa' must correspond to the company for which the PGR was issued. Extract only the legal name — remove any text in parentheses and remove all trailing punctuation. Preserve dots and punctuation within abbreviations like 'SERV.EQUIP.IND.COM.SA'.\n"
        "- 'autor': look for the person labeled as 'Responsável Técnico'. If not found, look for 'Elaborado por'. If not found, look for the main signer of the document. Extract ONLY the person's full name — do NOT include titles like Dr., Eng., CRM, CREA numbers, or any role descriptions.\n"
        "- Convert any Brazilian date formats (e.g., DD/MM/YYYY or DD/MM/YY) to ISO 8601 format (YYYY-MM-DD).\n"
        "- If the date contains only month and year (e.g., 'Janeiro de 2025'), use the first day of that month (e.g., 2025-01-01).\n"
        "- If multiple dates appear, prioritize the document expiration or validity date (vigência).\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> PGRData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=PGRData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore