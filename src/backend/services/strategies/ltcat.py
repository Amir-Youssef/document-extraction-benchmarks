from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.ltcat import LTCATData


class LTCATExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for Brazilian LTCAT documents."""

    document_type: DocumentType = DocumentType.LTCAT

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian occupational safety documents.\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- empresa: legal name of the company exactly as written on the document\n"
        "- data: date when the document expires or loses its validity\n"
        "- autor: full name of the responsible technical author or signing professional\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- 'empresa' must correspond to the company for which the LTCAT was issued. Extract only the legal name — remove any text in parentheses after the name.\n"
        "- 'autor' must correspond to the responsible technical professional who authored or signed the document. Extract ONLY the person's name — do NOT include professional titles like Dr., Eng., or job descriptions like 'médico do trabalho' or 'engenheiro de segurança'.\n"
        "- Convert any Brazilian date formats (e.g., DD/MM/YYYY or DD/MM/YY) to ISO 8601 format (YYYY-MM-DD).\n"
        "- If the date contains only month and year (e.g., 'Janeiro de 2020'), use the last day of that month (e.g., 2020-01-31).\n"
        "- If multiple dates appear, prioritize the document expiration or validity date (vigência).\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> LTCATData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=LTCATData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore