from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.seguro import SeguroData


class SeguroExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from an insurance policy document."""

    document_type: DocumentType = DocumentType.SEGURO

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian insurance documents (Apólice de Seguro).\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- nome: full name of the insured person or company exactly as written on the document\n"
        "- documento: identification document number of the insured\n"
        "- data: expiration date of the insurance policy\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- 'nome' must refer to the insured (segurado), not the insurance company or broker. Extract exactly as written, preserving dots in abbreviations like 'S.A.' or 'Ltda.'.\n"
        "- 'documento' must be extracted and formatted correctly. If it is a CPF (11 digits), format as XXX.XXX.XXX-XX. If it is a CNPJ (14 digits), format as XX.XXX.XXX/XXXX-XX. If the number appears without formatting in the document, apply the correct format based on the number of digits. Return ONLY the formatted number — do NOT append labels like '(CPF)', '(CNPJ)' or any other text after the number.\n"
        "- 'data' must be the policy expiration date (data de vencimento or vigência até). Convert any Brazilian date formats to ISO 8601 format (YYYY-MM-DD).\n"
        "- If multiple dates appear, prioritize the end of validity date.\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> SeguroData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=SeguroData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore