from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile

from backend.api.dependencies import get_orchestrator
from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.dto.extract_response import ExtractedDocument
from backend.services.orchestrator import DocumentOrchestrator

router = APIRouter(prefix="/v1", tags=["extraction"])


@router.post("/extract", response_model=ExtractedDocument)
async def extract_document(
    file: UploadFile,
    document_type: Annotated[DocumentType, Form()],
    orchestrator: Annotated[DocumentOrchestrator, Depends(get_orchestrator)],
    llm_model: Annotated[LLMModel | None, Form()] = None,
) -> ExtractedDocument:
    """Extract structured data from an uploaded document."""
    file_content = await file.read()

    data = await orchestrator.extract(
        document_type=document_type,
        file_content=file_content,
        llm_model=llm_model,
    )

    return ExtractedDocument(
        document_type=document_type,
        data=data.model_dump(mode="json"),
    )
