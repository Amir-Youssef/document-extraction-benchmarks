from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.arrais import ArraisData


class ArraisExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from an Arrais license."""

    document_type: DocumentType = DocumentType.ARRAIS

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of a ASO.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed on the document.\n"
        "- cpf: CPF number of the employee in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- data: date of validity of the document in YYYY-MM-DD format.\n"
        "- numero_registro: registration number exactly as printed on the document.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return an empty string for text fields.\n"
        "- Dates must be formatted strictly as YYYY-MM-DD.\n"
        "- CPF must be returned in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- Respond strictly with the structured output. No additional text.\n"
        "- After extracting all fields, re-check the cpf and data fields by reading them again from the document. "
        "If the second reading differs from the first, perform a third reading and use this third result as the final value."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> ArraisData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=ArraisData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore