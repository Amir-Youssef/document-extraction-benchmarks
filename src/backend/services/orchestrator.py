from pydantic import BaseModel

from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.services.factory import ExtractorFactory
from backend.services.text_normalizer import normalize_model


class DocumentOrchestrator:
    """Coordinates the document extraction flow.

    Acts as the main use-case entry point, delegating document-specific
    logic to the appropriate strategy obtained from the factory.
    """

    def __init__(self, factory: ExtractorFactory) -> None:
        self._factory = factory

    async def extract(
        self,
        *,
        document_type: DocumentType,
        file_content: bytes,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        """Execute the full extraction pipeline for a document.

        Args:
            document_type: The type of document being processed.
            file_content: Raw bytes of the uploaded document.
            llm_model: Optional LLM model override.

        Returns:
            A Pydantic model with the extracted structured data.
        """
        strategy = self._factory.get_strategy(document_type)
        result = await strategy.extract(file_content, llm_model=llm_model)
        return normalize_model(result)
