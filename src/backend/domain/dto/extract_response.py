from typing import Any

from pydantic import BaseModel

from backend.domain.enumx.document_type import DocumentType


class ExtractedDocument(BaseModel):
    """Base response model for extracted document data."""

    document_type: DocumentType
    data: dict[str, Any]
