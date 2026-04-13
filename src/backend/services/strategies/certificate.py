from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.certificate import CertificateData
from backend.domain.enumx.document_type import DocumentType


class CertificateExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a Brazilian Certificate."""

    document_type: DocumentType = DocumentType.CERTIFICATE

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of a Certificate.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed on the document.\n"
        "- cpf: CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- data: signature date or document date in YYYY-MM-DD format.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return an empty string for text fields.\n"
        "- Dates must be formatted strictly as YYYY-MM-DD.\n"
        "- CPF must be returned in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- Respond strictly with the structured output. No additional text."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> CertificateData:
        """Extract Certificate data from raw document bytes via the LLM client."""
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=CertificateData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore
