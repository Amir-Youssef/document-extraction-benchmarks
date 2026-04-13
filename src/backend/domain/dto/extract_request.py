from pydantic import BaseModel

from backend.domain.enumx.document_type import DocumentType


class ExtractDocumentRequest(BaseModel):
    """Request model for document extraction. File handling belongs to the API layer."""

    document_type: DocumentType
