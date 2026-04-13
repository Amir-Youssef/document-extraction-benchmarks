from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.cracha import CrachaData


class CrachaExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from an operator badge (crachá)."""

    document_type: DocumentType = DocumentType.CRACHA

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of an operator badge (crachá de operador).\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed on the badge.\n"
        "- cpf: CPF number in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- rg: RG (identity document) number exactly as printed.\n"
        "- treinamento: name of the training exactly as printed on the badge.\n"
        "- carga_horaria: training workload in the format 'x horas' (e.g., '24 horas').\n"
        "- data: date shown on the badge in YYYY-MM-DD format.\n"
        "- assinado: whether the badge contains a visible signature (true/false).\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return null.\n"
        "- Dates must be formatted strictly as YYYY-MM-DD.\n"
        "- CPF must be returned in Brazilian format (XXX.XXX.XXX-XX).\n"
        "- Respond strictly with the structured output. No additional text."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> CrachaData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=CrachaData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore
