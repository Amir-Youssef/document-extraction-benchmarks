from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.epi import EPIData


class EPIExtractionStrategy(DocumentExtractionStrategy):
    """Extraction strategy for EPI delivery forms (Ficha de Entrega de EPI)."""

    document_type: DocumentType = DocumentType.EPI

    SYSTEM_PROMPT: str = (
    "You are an AI specialized in strict data extraction from Brazilian EPI delivery forms.\n"
    "These documents have varied layouts: typed, handwritten, scanned, or mixed.\n"
    "Return ONLY raw JSON. No markdown, no explanation.\n\n"

    "Fields: nome, cpf, funcao, data, assinado\n\n"

    "DATA RULES (follow this priority order):\n"
    "1. If the document has an employee signature with a date nearby → use that date\n"
    "   Look for: 'Ass. do Funcionário', 'Assinatura do colaborador', 'Assinatura do Empregado'\n"
    "2. If there is no date near the signature → use the first date that appears in the document\n"
    "   (header, declaration block, or first table row)\n"
    "3. If no date exists anywhere in the document → null\n"
    "- Convert any format to YYYY-MM-DD\n"
    "- WRONG: using expiration date, last table date, or validity date\n"
    "- WRONG: using 'Data de devolução' or renewal dates\n\n"

    "NOME RULES:\n"
    "- Copy EXACTLY as printed, even if it appears to be a typo or OCR error\n"
    "- Do NOT autocorrect, complete, or add surnames not visible\n"
    "- Look for: 'Nome do Funcionário', 'Funcionário', 'NOME'\n"
    "- WRONG: 'Giuliano Rodrigues Ferrari' when doc shows 'Giuliano Rodrigues'\n"
    "- WRONG: 'Luiz Carlos de Paula Souza' when doc shows 'Luiz Carlos de Paula'\n"
    "- WRONG: 'Regis Canton' when doc shows 'Regis Cantor'\n\n"

    "CPF RULES:\n"
    "- If CPF is explicitly printed → return as XXX.XXX.XXX-XX\n"
    "- If CPF field is blank, absent, or not found → return ''\n"
    "- NEVER return null or 'none' for CPF\n\n"

    "FUNCAO RULES:\n"
    "- Copy EXACTLY as printed, including abbreviations and typos\n"
    "- Look for: 'Função', 'Setor/Função', 'Cargo'\n"
    "- WRONG: correcting 'tranmissao' to 'transmissao'\n"
    "- WRONG: correcting 'eletrecista' to 'eletricista'\n\n"

    "ASSINADO RULES:\n"
    "- true: visible handwritten mark or signature image near employee signature field\n"
    "- false: signature field present but clearly empty\n"
    "- null: no signature field found\n\n"

    "EXAMPLE (typed document - CPFL layout):\n"
    "{\n"
    '  "nome": "ALEX DOS SANTOS CONCEIÇÃO",\n'
    '  "cpf": "",\n'
    '  "funcao": "MONTADOR II",\n'
    '  "data": "2024-01-25",\n'
    '  "assinado": true\n'
    "}\n\n"

    "EXAMPLE (handwritten document - Bioglobal layout):\n"
    "{\n"
    '  "nome": "LUCIANO OCAMPO MANDRACIO",\n'
    '  "cpf": "",\n'
    '  "funcao": "ANALISTA AMBIENTAL",\n'
    '  "data": "2023-10-16",\n'
    '  "assinado": true\n'
    "}\n\n"

    "Missing fields → null, except cpf → ''\n"
)

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> EPIData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=EPIData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore