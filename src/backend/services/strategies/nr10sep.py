from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.nr10sep import NR10SEPData


class NR10SEPExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a NR-10 SEP certificate."""

    document_type: DocumentType = DocumentType.NR10SEP

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of a NR-10 SEP training certificate.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed on the document.\n"
        "- cpf: CPF or CNPJ number of the holder in Brazilian format (CPF: XXX.XXX.XXX-XX or CNPJ: XX.XXX.XXX/XXXX-XX).\n"
        "- data: training completion date in YYYY-MM-DD format.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return an empty string for text fields.\n"
        "- Dates must be formatted strictly as YYYY-MM-DD.\n"
        "- CPF or CNPJ must be returned in Brazilian format.\n"
        "- Respond strictly with the structured output. No additional text."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> NR10SEPData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NR10SEPData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore