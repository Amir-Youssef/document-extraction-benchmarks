class DocExtractorError(Exception):
    """Base exception for the Doc Extractor domain."""


class DocumentUnreadableError(DocExtractorError):
    """Raised when a document cannot be read or parsed."""


class UnsupportedDocumentTypeError(DocExtractorError):
    """Raised when the provided document type is not supported."""
