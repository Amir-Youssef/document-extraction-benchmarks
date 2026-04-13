from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.ficha_registro import FichaRegistroData


class FichaRegistroExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for Brazilian Employee Registration Forms (Ficha de Registro)."""

    document_type: DocumentType = DocumentType.FICHA_REGISTRO

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured information from Brazilian labor documents.\n\n"

        "Analyze the document and extract ONLY the fields defined below.\n\n"

        "Fields to extract:\n"
        "- nome_empregado: full name of the employee exactly as written on the document\n"
        "- nome_empregador: legal name of the employer/company\n"
        "- cpf_empregado: CPF number of the employee in format XXX.XXX.XXX-XX.\n"
        "- cargo: job title or position of the employee\n"
        "- data_admissao: employee hiring/admission date\n\n"

        "Extraction rules:\n"
        "- Extract only information that is explicitly visible in the document.\n"
        "- Do NOT guess, infer, or fabricate any values.\n"
        "- If a field cannot be clearly identified, return null.\n"
        "- 'nome_empregado' must refer to the registered employee, not supervisors or HR staff.\n"
        "- 'nome_empregador': check both the 'razão social' field and any stamp/carimbo present in the document. Use the shortest and most concise version that appears — do NOT include full legal suffixes like 'Industria e Comercio S.A.' unless they are part of the razão social field itself. Preserve internal commas but remove only trailing commas or periods at the end of the name.\n"
        "- 'cargo': if the employee had only one position, extract it. If multiple positions appear over time, extract only the most recent one. If the cargo ends with 'GERA', complete it to 'GERAL'.\n"
        "- CPF must follow the Brazilian format XXX.XXX.XXX-XX. If it appears without formatting, apply the format.\n"
        "- Convert any Brazilian date formats (e.g., DD/MM/YYYY or DD/MM/YY) to DD/MM/YYYY format.\n"
        "- If multiple dates appear, prioritize the hiring/admission date (data de admissão).\n\n"

        "Return only structured data that matches the provided schema."
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> FichaRegistroData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=FichaRegistroData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore