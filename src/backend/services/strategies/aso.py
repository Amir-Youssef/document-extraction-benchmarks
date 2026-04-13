from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.aso import ASOData

class ASOExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a ASO."""

    document_type: DocumentType = DocumentType.ASO

    SYSTEM_PROMPT: str = (
    "You are a document analysis specialist for Brazilian documents. "
    "You are receiving an image or PDF of a ASO.\n\n"
    "Your task is to extract ONLY the following fields:\n"
    "- nome: the full name of the holder, exactly as printed on the document.\n"
    "- cpf: CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).\n"
    "- apto: whether the worker is declared fit or unfit for the position, return only 'APTO' or 'INAPTO'.\n"
    "- data: document signature date in YYYY/MM/DD format.\n"
    "- funcao: the job title or function of the employee exactly as printed in the document, only the function name without digits.\n\n"
    "Rules:\n"
    "- Extract only what is explicitly visible in the document.\n"
    "- Do NOT infer, guess, or fabricate any data.\n"
    "- If a field is not legible or not present, return a 'none' string.\n"
    "- Dates must be formatted strictly as YYYY-MM-DD.\n"
    "- CPF must be returned in Brazilian format (XXX.XXX.XXX-XX).\n"
    "- If a number appears labeled as 'RG' but matches the CPF pattern (XXX.XXX.XXX-XX), treat it as CPF and extract it as cpf.\n"
    "- Respond strictly with the structured output. No additional text."
)

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> ASOData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=ASOData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore