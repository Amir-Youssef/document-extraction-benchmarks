from abc import ABC, abstractmethod

from pydantic import BaseModel

from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel


class LLMClient(ABC):
    """Contract for LLM communication.

    The domain delegates structured extraction to an LLM through
    this interface, keeping infrastructure details out of the core logic.
    """

    @abstractmethod
    async def extract_structured(
        self,
        *,
        content: bytes,
        output_model: type[BaseModel],
        system_prompt: str,
        llm_model: LLMModel | None = None,
    ) -> BaseModel:
        """Send content to an LLM and receive validated structured output.

        Args:
            content: Raw bytes of the document (image or PDF).
            output_model: The Pydantic model class the LLM must conform to.
            system_prompt: Instructions that guide the LLM extraction.
            llm_model: Optional model override; uses default when ``None``.

        Returns:
            An instance of ``output_model`` with the extracted data.
        """
        ...


class DocumentExtractionStrategy(ABC):
    """Contract for document extraction strategies.

    Each supported document type must have a concrete strategy
    that knows how to extract structured data from raw file bytes.
    """

    document_type: DocumentType

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    @abstractmethod
    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> BaseModel:
        """Extract structured data from raw document bytes.

        Args:
            file_content: Raw bytes of the uploaded document.
            llm_model: Optional LLM model override.

        Returns:
            A Pydantic model containing the extracted fields.
        """
        ...
