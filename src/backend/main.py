from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers.document_types import router as document_types_router
from backend.api.routers.extract import router as extract_router
from backend.api.routers.health import router as health_router
from backend.api.routers.llm_models import router as llm_models_router
from backend.core.config import settings
from backend.core.exceptions import DocumentUnreadableError, UnsupportedDocumentTypeError
from backend.core.logging import setup_logging

setup_logging(settings)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(extract_router)
app.include_router(document_types_router)
app.include_router(llm_models_router)


@app.exception_handler(UnsupportedDocumentTypeError)
async def unsupported_document_type_handler(
    _request: Request,
    exc: UnsupportedDocumentTypeError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(DocumentUnreadableError)
async def document_unreadable_handler(
    _request: Request,
    exc: DocumentUnreadableError,
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})
