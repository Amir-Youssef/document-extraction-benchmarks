from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.pcmso import PCMSOData


class PCMSOExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a PCMSO."""

    document_type: DocumentType = DocumentType.PCMSO

    SYSTEM_PROMPT: str = (
    "You are an AI specialized in extracting structured data from Brazilian PCMSO documents with noisy OCR and inconsistent layouts.\n\n"

    "Fields to extract: nome_empresa, cnpj, responsavel_empresa, data, assinado\n\n"

    "DATE RULES:\n"
    "- Target field: expiration or validity date of the PCMSO program\n"
    "- Look for: 'validade', 'vencimento', 'válido até', 'vigência até', 'período de vigência'\n"
    "- Do NOT use elaboration, emission, or signature dates unless no validity date exists\n"
    "- Year only (e.g. '2020') → 'YYYY-01-01'\n"
    "- Month+year only (e.g. '01/2020') → 'YYYY-MM-01'\n"
    "- DD/MM/YYYY → YYYY-MM-DD\n"
    "- If genuinely not found → null\n\n"

    "RESPONSAVEL RULES:\n"
    "- Extract ONLY the company representative (e.g. diretor, gerente, responsável legal)\n"
    "- Do NOT extract doctors, medical coordinators, or PCMSO responsible physicians\n"
    "- If no company representative is explicitly identified → null\n\n"

    "ASSINADO RULES:\n"
    "- true: visible signature image or handwritten mark is present\n"
    "- false: signature field exists but is empty or blank\n"
    "- null: no signature field or indicator found anywhere in the document\n\n"

    "CNPJ RULES:\n"
    "- Numbers only, no punctuation. Example: '58635517000137'\n"
    "- Search entire document including headers and footers\n"
    "- If not found → null\n\n"

    "GENERAL RULES:\n"
    "- Handle OCR noise: broken words, missing accents, spacing issues\n"
    "- Search the entire document including headers, footers, stamps, and signature blocks\n"
    "- If a field is genuinely absent → null. Never fabricate or infer values\n"
    "- Return only structured data matching the schema\n"
)

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> PCMSOData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=PCMSOData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore