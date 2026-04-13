from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.nr33 import NR33Data


class NR33ExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a NR-33 training certificate."""

    document_type: DocumentType = DocumentType.NR33

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian occupational safety training certificates.\n"
        "You are receiving an image or PDF of a NR-33 certificate.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the certificate holder, exactly as printed. Remove any trailing punctuation.\n"
        "- cpf: the CPF number in format XXX.XXX.XXX-XX. Return null if not present. Extract only the digits that are clearly visible — do NOT complete, guess or fabricate missing digits.\n"
        "- curso: the core course name only. Remove any prefixes like 'NR33', 'NR 33', 'NR-33', 'Reciclagem', 'Curso de', 'Periódico'. Remove content in parentheses. Preserve hyphens between words. Remove any trailing punctuation.\n"
        "- data: training completion date in YYYY-MM-DD format.\n"
        "- carga_horaria: duration as written only this format (e.g. '24 horas' '8 horas' '10 horas')\n"
        "- empresa: the name of the company WHERE THE EMPLOYEE WORKS, not the training center or clinic. Look for fields like 'Empresa', 'Empregador' or 'Razão Social'. Extract ONLY the company name — do NOT include labels like 'Empresa:' or 'Empregador:'. Remove all trailing punctuation including periods, commas and hyphens.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return null.\n"
        "- Respond strictly with the structured output. No additional text."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> NR33Data:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NR33Data,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore