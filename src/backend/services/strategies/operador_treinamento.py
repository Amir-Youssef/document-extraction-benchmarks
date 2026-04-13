from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.operador_treinamento import OperadorTreinamentoData


class OperadorTreinamentoExtractionStrategy(DocumentExtractionStrategy):
    """Strategy for extracting operator training documents."""

    document_type: DocumentType = DocumentType.OPERADOR_TREINAMENTO

    SYSTEM_PROMPT: str = (
        "You are an AI specialized in extracting structured data from Brazilian operator ID cards (crachás/carteirinhas).\n"
        "These are small two-sided cards issued by training companies like Motriz Treinamentos.\n"
        "Return ONLY raw JSON. No markdown, no explanation.\n\n"
        "Fields: nome, cpf, rg, treinamento, carga_horaria, data, assinado\n\n"
        "DOCUMENT STRUCTURE:\n"
        "- Left side: date written in full (e.g. 'Maravilha - Sc. 17 de Junho de 2023'), instructor signatures\n"
        "- Right side: NOME, CPF or RG, OPERADOR (equipment/training name), CARGA HORÁRIA\n\n"
        "DATA RULES:\n"
        "- Extract the date written in full on the left side of the card\n"
        "- This date is the ISSUE date — add exactly 1 year to get the EXPIRATION date\n"
        "- Format: 'DD de [month] de YYYY' → convert to YYYY-MM-DD, then add 1 year\n"
        "- RIGHT: 'Maravilha - Sc. 17 de Junho de 2023' → '2024-06-17'\n"
        "- RIGHT: 'Concordia - SC. 12 de Janeiro de 2025' → '2026-01-12'\n\n"
        "NOME RULES:\n"
        "- Extract from the 'NOME:' field on the right side\n"
        "- Copy EXACTLY as printed, including abbreviations with dots\n"
        "- RIGHT: 'Lucas E. da R. Bortoletti' (not expanded)\n"
        "- RIGHT: 'Carlos I. L. Borboletti' (not corrected to Bortoletti)\n\n"
        "CPF RULES:\n"
        "- Extract from 'CPF:' field on the right side\n"
        "- Keep punctuation as printed: XXX.XXX.XXX-XX\n"
        "- If CPF field is absent, blank, or not found → null (JSON null, not the string 'null' or '')\n\n"
        "RG RULES:\n"
        "- Extract from 'RG:' field on the right side\n"
        "- Copy digits exactly as printed\n"
        "- If RG field is absent or blank → null (JSON null, not the string 'null')\n\n"
        "TREINAMENTO RULES:\n"
        "- Extract from 'OPERADOR:' field on the right side\n"
        "- Copy EXACTLY as printed, including abbreviations and NR format as written\n"
        "- Remove any trailing punctuation (dots, commas) at the end of the value\n"
        "- WRONG: 'Caminhão Guindauto Nr11.' → RIGHT: 'Caminhão Guindauto Nr11'\n"
        "- WRONG: expanding 'Escavadeira H.' to 'Escavadeira Hidraulica'\n"
        "- WRONG: normalizing 'Nr11' to 'NR-11'\n\n"
        "CARGA_HORARIA RULES:\n"
        "- Extract from 'CARGA HORÁRIA:' field\n"
        "- Copy exactly as printed (e.g. '24 Horas')\n\n"
        "ASSINADO RULES:\n"
        "- true: visible handwritten signatures present on the left side\n"
        "- false: signature fields present but empty\n"
        "- null: no signature fields found\n\n"
        "EXAMPLES:\n"
        "{\n"
        '  "nome": "Lucas E. da R. Bortoletti",\n'
        '  "cpf": "090.271.369-80",\n'
        '  "rg": null,\n'
        '  "treinamento": "Caminhão Guindauto Nr11",\n'
        '  "carga_horaria": "24 Horas",\n'
        '  "data": "2024-06-17",\n'
        '  "assinado": true\n'
        "}\n"
        "{\n"
        '  "nome": "Giovanni Sauer",\n'
        '  "cpf": null,\n'
        '  "rg": "6615685",\n'
        '  "treinamento": "Escavadeira Hidraulica",\n'
        '  "carga_horaria": "24 Horas",\n'
        '  "data": "2022-11-06",\n'
        '  "assinado": true\n'
        "}\n\n"
        "Missing fields → null (JSON null, never the string 'null' or empty string '')\n"
    )

    async def extract(
        self,
        file_content: bytes,
        *,
        llm_model: LLMModel | None = None,
    ) -> OperadorTreinamentoData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=OperadorTreinamentoData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore