# Doc Extractor

Full-stack application for uploading documents (PDFs or images), identifying their type, and extracting structured data using LLMs (Google Gemini via Pydantic AI).

Send a photo of a Brazilian document → receive a validated JSON with the extracted fields.

```
┌──────────┐                             ┌────────────────┐      Gemini       ┌──────────┐
│ Frontend │     POST /v1/extract        │    Backend     │  ──────────────▶  │  Google  │
│  (React) │  ───────────────────────▶   │   (FastAPI)    │   structured out  │  Gemini  │
└──────────┘    file + document_type     └────────────────┘                   └──────────┘
                  + llm_model (opt)             │
                                                ▼
                                         Structured JSON
                                       (Pydantic validated)
```

---

## Technologies Used

### Backend

| Technology | Role |
|---|---|
| **Python 3.12+** | Main language |
| **FastAPI** | Web framework (endpoints, DI, validation, CORS) |
| **Pydantic v2** | Data validation and domain models |
| **Pydantic AI** | LLM call orchestration (provider-agnostic) |
| **Google Gemini** | Multimodal LLM (vision + text) via `pydantic-ai[google]` |
| **pydantic-settings** | Configuration management via environment variables |
| **uv** | Dependency and virtualenv management |
| **Docker** | Containerization (multi-stage production + dev) |

### Frontend

| Technology | Role |
|---|---|
| **TypeScript** | Language (strict mode) |
| **React 19** | UI framework (functional components, hooks) |
| **Vite 7** | Build tool and dev server |
| **ESLint 9** | Linting with `typescript-eslint`, `react-hooks`, `react-refresh` |

---

## Architecture

The system follows **SOLID** principles with core design patterns:

| Pattern | Class | Responsibility |
|---|---|---|
| **Strategy** | `DocumentExtractionStrategy` | Each document type has its own extraction strategy |
| **Factory** | `ExtractorFactory` | Maps `DocumentType` → Strategy and instantiates with `LLMClient` |
| **Orchestrator** | `DocumentOrchestrator` | Coordinates flow: receives request → obtains strategy → executes → returns |
| **Model Factory** | `ModelFactory` | Abstracts LLM model construction by provider |

### Layer Separation (Backend)

```
api/          → HTTP layer (FastAPI). Thin routers, DI, input validation.
domain/       → Pure layer. Pydantic models, enums, interfaces (ABC). Zero external dependencies.
services/     → Business logic. Factory, Orchestrator, concrete Strategies.
infra/        → I/O adapters. LLMClient implementation using Pydantic AI + Gemini.
core/         → Global configuration. Settings, logging, domain exceptions.
```

The domain **never** imports FastAPI, Pydantic AI, or any infrastructure library. Communication with LLMs is done exclusively through the `LLMClient` interface (ABC), implemented by `PydanticAILLMClient` in the infrastructure layer.

### Frontend

- **SPA** with pure React (no routing library).
- **API-driven UI**: document types and LLM models are dynamically loaded from the backend (`GET /v1/document-types`, `GET /v1/llm-models`), so the frontend **never** hardcodes domain options.
- **Fetch-based API client** in `api.ts` with error handling (parses `detail` from JSON response).

---

## Folder Structure

The project is a **monorepo** with two independent applications in `src/`:

```
src/
├── backend/                         # Python — FastAPI REST API
│   ├── main.py                      # App factory, CORS, exception handlers, router registration
│   ├── api/
│   │   ├── dependencies.py          # Complete DI chain (Settings → ModelFactory → LLMClient → Factory → Orchestrator)
│   │   └── routers/
│   │       ├── health.py            # GET /health
│   │       ├── extract.py           # POST /v1/extract
│   │       ├── document_types.py    # GET /v1/document-types
│   │       └── llm_models.py        # GET /v1/llm-models
│   ├── core/
│   │   ├── config.py                # Settings (pydantic-settings), MODEL_IDENTIFIERS mapping
│   │   ├── logging.py               # Structured logging
│   │   └── exceptions.py            # Domain exception hierarchy (DocExtractorError base)
│   ├── domain/
│   │   ├── interfaces.py            # ABCs: LLMClient, DocumentExtractionStrategy
│   │   ├── enumx/
│   │   │   ├── document_type.py     # DocumentType enum (cnh, aso, certificate)
│   │   │   └── llm_model.py         # LLMModel enum (gemini-pro, gemini-flash)
│   │   ├── dto/
│   │   │   ├── extract_request.py   # ExtractDocumentRequest
│   │   │   └── extract_response.py  # ExtractedDocument
│   │   └── models/
│   │       ├── cnh.py               # CNHData (Pydantic model)
│   │       └── certificate.py       # CertificateData (Pydantic model)
│   ├── services/
│   │   ├── factory.py               # ExtractorFactory
│   │   ├── orchestrator.py          # DocumentOrchestrator
│   │   └── strategies/
│   │       ├── cnh.py               # CNHExtractionStrategy
│   │       └── certificate.py       # CertificateExtractionStrategy
│   └── infra/
│       └── llm/
│           ├── gemini_client.py     # PydanticAILLMClient (Pydantic AI adapter)
│           └── model_factory.py     # ModelFactory (builds Model instances by provider)
└── frontend/                        # TypeScript — React SPA
    ├── index.html                   # Entry HTML (Vite SPA)
    ├── package.json                 # Dependencies & scripts
    ├── vite.config.ts               # Vite config (React plugin)
    ├── tsconfig.json                # TypeScript project references
    ├── tsconfig.app.json            # App TS config (strict mode)
    ├── eslint.config.js             # ESLint flat config
    └── src/
        ├── main.tsx                 # React root (StrictMode)
        ├── App.tsx                  # Main component (form, state, submit)
        ├── api.ts                   # API client (fetch-based, connects to backend)
        ├── types.ts                 # TypeScript interfaces (DocumentTypeOption, LLMModelOption, ExtractedDocument)
        └── index.css                # Global styles (minimal, system-ui)
```

---

## Prerequisites

- **Python** 3.12 or higher
- **uv** ([docs.astral.sh/uv](https://docs.astral.sh/uv/)) — Python package manager
- **Node.js** 18+ and **npm** — for the frontend
- **Google Gemini API Key** ([aistudio.google.com](https://aistudio.google.com/))
- **Docker** and **Docker Compose** (optional, for containerized execution)

---

## Installation and Configuration

### 1. Clone the repository

```bash
git clone <repository-url>
cd doc-extractor
```

### 2. Configure environment variables

All backend environment variables use the `DOC_EXTRACTOR_` prefix.

Create a `.env` file in the **project root**:

```env
DOC_EXTRACTOR_GEMINI_API_KEY=your-key-here
DOC_EXTRACTOR_DEFAULT_LLM_MODEL=gemini-pro
DOC_EXTRACTOR_ENVIRONMENT=development
DOC_EXTRACTOR_LOG_LEVEL=INFO
```

> ⚠️ **Never** commit API keys. The `.env` is already in `.gitignore`.

#### Available variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DOC_EXTRACTOR_GEMINI_API_KEY` | **Yes** | `""` | Google Gemini API key |
| `DOC_EXTRACTOR_DEFAULT_LLM_MODEL` | No | `gemini-pro` | Default LLM model (`gemini-pro` or `gemini-flash`) |
| `DOC_EXTRACTOR_APP_NAME` | No | `Doc Extractor API` | Application name |
| `DOC_EXTRACTOR_ENVIRONMENT` | No | `development` | Execution environment |
| `DOC_EXTRACTOR_LOG_LEVEL` | No | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### 3. Install dependencies

**Backend (Python):**

```bash
uv sync
```

**Frontend (Node.js):**

```bash
cd src/frontend
npm install
cd ../..
```

---

## How to Run Locally

### Backend

```bash
# Start API in development mode (hot reload on port 8000)
uv run fastapi dev src/backend/main.py

# Verify it's working
curl http://localhost:8000/health
# {"status":"ok"}
```

Interactive documentation (Swagger) will be available at: http://localhost:8000/docs

### Frontend

In another terminal:

```bash
cd src/frontend
npm run dev
```

The frontend will be available at: http://localhost:5173

> The frontend connects to the backend at `http://localhost:8000` (hardcoded in `api.ts`). Make sure the backend is running before using the frontend.

---

## How to Run with Docker

Docker Compose has two services: **production** and **development**.

### Production

The production Dockerfile uses a **multi-stage build** (builder → slim runtime with non-root user).

```bash
# Build and start
docker compose up --build

# Validate
curl http://localhost:8000/health
```

### Development

The development Dockerfile mounts the source code via volume for hot reload.

```bash
# Build and start with dev profile
docker compose --profile dev up --build
```

Default exposed port: **8000**.

> **Note:** Current Dockerfiles only cover the backend. The frontend should be run locally with `npm run dev` during development.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/v1/extract` | Extracts data from uploaded document |
| `GET` | `/v1/document-types` | Lists all supported document types |
| `GET` | `/v1/llm-models` | Lists all available LLM models |

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### List document types

```bash
curl http://localhost:8000/v1/document-types
```

```json
[
  {"value": "cnh", "label": "Carteira Nacional de Habilitação"},
  {"value": "aso", "label": "Atestado de Saúde Ocupacional"},
  {"value": "certificate", "label": "Certificado"}
]
```

### List LLM models

```bash
curl http://localhost:8000/v1/llm-models
```

```json
[
  {"value": "gemini-pro", "label": "Gemini 3 Pro"},
  {"value": "gemini-flash", "label": "Gemini 3 Flash"}
]
```

### Extract document data

```
POST /v1/extract
Content-Type: multipart/form-data
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | `UploadFile` | Yes | Document file (PDF, PNG, JPEG, WEBP) |
| `document_type` | `string` | Yes | Document type: `cnh`, `aso`, `certificate` |
| `llm_model` | `string` | No | LLM model: `gemini-pro` or `gemini-flash` (uses default if omitted) |

#### Example with curl

```bash
curl -X POST http://localhost:8000/v1/extract \
  -F "file=@/path/to/cnh.pdf" \
  -F "document_type=cnh" \
  -F "llm_model=gemini-flash"
```

#### Response example (CNH)

```json
{
  "document_type": "cnh",
  "data": {
    "nome": "MARIA DA SILVA SANTOS",
    "numero_registro": "00123456789",
    "cpf": "12345678901",
    "data_validade": "2028-12-31"
  }
}
```

#### Response example (Certificate)

```json
{
  "document_type": "certificate",
  "data": {
    "nome": "JOÃO PEDRO OLIVEIRA",
    "cpf": "98765432100",
    "data": "2025-06-15"
  }
}
```

---

## Supported Document Types

| Type | Enum | Pydantic Model | Strategy | Extracted Fields |
|---|---|---|---|---|
| CNH | `cnh` | `CNHData` | `CNHExtractionStrategy` | `nome`, `numero_registro`, `cpf`, `data_validade` |
| Certificate | `certificate` | `CertificateData` | `CertificateExtractionStrategy` | `nome`, `cpf`, `data` |
| ASO | `aso` | *(no strategy yet)* | — | — |

## Available LLM Models

| Enum | Provider Identifier | Label |
|---|---|---|
| `gemini-pro` | `gemini-3-pro-preview` | Gemini 3 Pro |
| `gemini-flash` | `gemini-3-flash-preview` | Gemini 3 Flash |

---

## How to Contribute

### Adding a New Document Type

The system is designed so that adding a new document type **does not require changing endpoints, Orchestrator, or frontend**. It takes 6 steps:

#### 1. Create the Pydantic model

File: `src/backend/domain/models/novo_documento.py`

> Each field **must** have a `description` — this is what guides the LLM during extraction.

```python
from datetime import date
from pydantic import BaseModel, Field


class NovoDocumentoData(BaseModel):
    """Structured data extracted from the new document type."""

    nome: str = Field(
        description="Full name of the holder, exactly as printed on the document.",
    )
    campo_especifico: str = Field(
        description="Description that guides the LLM to extract this field correctly.",
    )
    data: date = Field(
        description="Relevant date in ISO 8601 format (YYYY-MM-DD).",
    )
```

#### 2. Re-export in `__init__.py`

In `src/backend/domain/models/__init__.py`:

```python
from backend.domain.models.novo_documento import NovoDocumentoData

__all__ = [
    "CNHData",
    "CertificateData",
    "NovoDocumentoData",  # new
]
```

#### 3. Add member to `DocumentType` enum

In `src/backend/domain/enumx/document_type.py`:

```python
class DocumentType(str, Enum):
    CNH = "cnh"
    ASO = "aso"
    CERTIFICATE = "certificate"
    NOVO_DOCUMENTO = "novo_documento"  # new
```

#### 4. Create the Strategy

File: `src/backend/services/strategies/novo_documento.py`

```python
from backend.domain.enumx.document_type import DocumentType
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.interfaces import DocumentExtractionStrategy
from backend.domain.models.novo_documento import NovoDocumentoData


class NovoDocumentoExtractionStrategy(DocumentExtractionStrategy):
    """Concrete strategy for extracting structured data from a NovoDocumento."""

    document_type: DocumentType = DocumentType.NOVO_DOCUMENTO

    SYSTEM_PROMPT: str = (
        "You are a document analysis specialist for Brazilian documents. "
        "You are receiving an image or PDF of a NovoDocumento.\n\n"
        "Your task is to extract ONLY the following fields:\n"
        "- nome: the full name of the holder, exactly as printed.\n"
        "- campo_especifico: description of the specific field.\n"
        "- data: the relevant date in YYYY-MM-DD format.\n\n"
        "Rules:\n"
        "- Extract only what is explicitly visible in the document.\n"
        "- Do NOT infer, guess, or fabricate any data.\n"
        "- If a field is not legible or not present, return an empty string for text fields.\n"
        "- Respond strictly with the structured output. No additional text."
    )

    async def extract(
        self, file_content: bytes, *, llm_model: LLMModel | None = None,
    ) -> NovoDocumentoData:
        return await self._llm_client.extract_structured(
            content=file_content,
            output_model=NovoDocumentoData,
            system_prompt=self.SYSTEM_PROMPT,
            llm_model=llm_model,
        )  # type: ignore
```

#### 5. Register in Factory

In `src/backend/services/factory.py`, add to `_types_registry`:

```python
from backend.services.strategies.novo_documento import NovoDocumentoExtractionStrategy

# Inside __init__:
self._types_registry = {
    DocumentType.CNH: CNHExtractionStrategy,
    DocumentType.CERTIFICATE: CertificateExtractionStrategy,
    DocumentType.NOVO_DOCUMENTO: NovoDocumentoExtractionStrategy,  # new
}
```

#### 6. Add readable label

In `src/backend/api/routers/document_types.py`, add to `DOCUMENT_TYPE_LABELS`:

```python
DOCUMENT_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.CNH: "Carteira Nacional de Habilitação",
    DocumentType.ASO: "Atestado de Saúde Ocupacional",
    DocumentType.CERTIFICATE: "Certificado",
    DocumentType.NOVO_DOCUMENTO: "Novo Documento",  # new
}
```

> **The `POST /v1/extract` endpoint, Orchestrator, and frontend do not need to be changed.** The new type will be automatically available in the UI and API.

---

### Adding a New LLM Model (Same Provider)

To add a new Google Gemini model (or any existing provider):

1. **Enum:** Add member in `src/backend/domain/enumx/llm_model.py`.
2. **Identifier:** Map in `src/backend/core/config.py` → `MODEL_IDENTIFIERS`.
3. **Builder:** Register in `ModelFactory._BUILDERS` in `src/backend/infra/llm/model_factory.py` (can reuse existing builder).
4. **Label:** Add readable label in `src/backend/api/routers/llm_models.py` → `LLM_MODEL_LABELS`.

### Adding a New LLM Provider (e.g., OpenAI, Anthropic)

1. Add a new private builder method in `ModelFactory` (e.g., `_build_openai`).
2. Register in `ModelFactory._BUILDERS` for the corresponding `LLMModel` members.
3. Add necessary configurations (API keys, etc.) in `src/backend/core/config.py`.

---

## Common Errors and Solutions

### Invalid or Missing API Key

```
ValidationError: API key required for Gemini Developer API
```

**Solution:** Set the `DOC_EXTRACTOR_GEMINI_API_KEY` environment variable with a valid key in the `.env` file.

### Document Type Without Strategy

```json
{"detail": "No extraction strategy registered for document type: 'aso'"}
```

**Solution:** The `aso` type is registered in the enum but doesn't have an implemented strategy yet. Follow the "Adding a New Document Type" guide to implement it.

### Frontend Doesn't Connect to Backend

If the frontend displays "Failed to load document types", check:
1. The backend is running on port 8000.
2. CORS is enabled (already enabled by default in development).
3. The `BASE_URL` in `src/frontend/src/api.ts` points to `http://localhost:8000`.

### Unsupported Document Type

```json
{"detail": "No extraction strategy registered for document type: 'aso'"}
```

**Cause:** The `DocumentType` exists in the enum but doesn't have a Strategy registered in the Factory.
**Solution:** Implement the corresponding Strategy and register it in the Factory.

### Pydantic Validation Error (422)

```json
{"detail": [{"type": "enum", "msg": "Input should be 'cnh', 'aso' or 'certificate'"}]}
```

**Cause:** The value sent in `document_type` doesn't match any enum member.
**Solution:** Use one of the accepted values: `cnh`, `aso`, `certificate`.

### Illegible Document

```json
{"detail": "Document could not be read or parsed"}
```

**Cause:** The uploaded file is corrupted, empty, or in an unsupported format.
**Solution:** Verify the file and send a legible PDF or image (PNG, JPEG, WEBP).

---

## Final Notes

### Best Practices Applied

- **SOLID** — Each class has a single responsibility; dependencies are injected via interfaces
- **100% type hints** on all functions and methods
- **Pure domain** — Models and interfaces without infrastructure dependencies
- **Structured Output** — The LLM returns a validated Pydantic object directly, never raw JSON


Implement LLM client caching (singleton in DI)