from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.escavadeira import EscavadeiraData


class EscavadeiraExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a hydraulic excavator operator training certificate."""

    document_type: DocumentType = DocumentType.ESCAVADEIRA
    
    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian occupational training certificates.\n"
        "You are receiving an image or PDF of a hydraulic excavator operator training certificate.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the certificate holder, exactly as printed.\n"
        "- cpf: the CPF number in format XXX.XXX.XXX-XX. Return null if not present.\n"
        "- curso: extract ONLY the course name exactly as printed. Preserve hyphens. Remove any trailing punctuation like commas or periods.\n"
        "- data: the training completion date. ALWAYS return in YYYY-MM-DD format. NEVER use DD/MM/YYYY. Do NOT use the expiration date.\n"
        "- carga_horaria: duration in the only format 'x horas' (e.g., '24 horas, 8 horas').\n"
        "- empresa: the name of the institution that issued the certificate, exactly as printed.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return null.\n"
        "- Respond strictly with the structured output. No additional text."
    )


    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> EscavadeiraData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=EscavadeiraData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore