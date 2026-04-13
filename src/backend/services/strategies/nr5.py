from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.nr5 import NR5Data


class NR5ExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a NR-5 certificate."""

    document_type: DocumentType = DocumentType.NR5

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of a NR-5 training certificate.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed on the document.\n"
        "- cpf: CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- treinamento: name of the training exactly as printed in the document. Format ('training name')\n"
        "- carga_horaria: total workload of the training exactly as printed in the document.\n"
        "- data: training completion date in YYYY-MM-DD format.\n\n"
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
    ) -> NR5Data:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NR5Data,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore