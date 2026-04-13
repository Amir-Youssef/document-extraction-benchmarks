---
applyTo: '**'
---
# Doc Extractor - Project Instructions & Standards

This file provides guidance to the AI Assistant when working with code in this repository.

## Project Overview

**Doc Extractor** is a full-stack application composed of a **RESTful API backend** and a **React SPA frontend**. The backend receives document uploads (PDFs or Images), identifies their type (e.g., ASO, CNH, Certificates), extracts structured information using LLMs (Google Gemini via Pydantic AI), and returns validated JSON data. The frontend provides a user-friendly web interface for uploading documents and viewing extracted results.

The primary goal is **extensibility**. Adding a new document type must be trivial, requiring only the creation of a new Strategy and a Data Model, without altering the API's main flow or the frontend code.

## Tech Stack

### Backend (`src/backend/`)
- **Language:** Python 3.12+
- **Package Manager:** `uv` (virtualenv management, lockfile-based installs)
- **Web Framework:** FastAPI (with CORS middleware enabled)
- **Data Validation:** Pydantic V2 (extensive use of `Field` and `BaseModel`)
- **LLM Orchestration:** Pydantic AI (`pydantic-ai`) — provider-agnostic agent framework
- **LLM Provider:** Google Gemini (via `pydantic-ai[google]`, using `GoogleModel` / `GoogleProvider`)
- **Settings Management:** `pydantic-settings` (env vars with `DOC_EXTRACTOR_` prefix)
- **Containerization:** Docker & Docker Compose (multi-stage production + dev images)
- **Testing:** Pytest

### Frontend (`src/frontend/`)
- **Language:** TypeScript (strict mode)
- **Framework:** React 19 (functional components, hooks)
- **Build Tool:** Vite 7
- **Linting:** ESLint 9 with `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- **Package Manager:** npm (standard `package.json`)

## Project Structure

The project is a **monorepo** with two independent applications under `src/`:

```
src/
├── backend/                         # Python — FastAPI REST API
│   ├── main.py                      # App factory, CORS, exception handlers, router registration
│   ├── api/
│   │   ├── dependencies.py          # Full DI chain (Settings → ModelFactory → LLMClient → Factory → Orchestrator)
│   │   └── routers/
│   │       ├── health.py            # GET /health
│   │       ├── extract.py           # POST /v1/extract
│   │       ├── document_types.py    # GET /v1/document-types (lists supported types)
│   │       └── llm_models.py        # GET /v1/llm-models (lists available LLM models)
│   ├── core/
│   │   ├── config.py                # Settings (pydantic-settings), MODEL_IDENTIFIERS mapping
│   │   ├── logging.py               # Structured logging setup
│   │   └── exceptions.py            # Domain exceptions hierarchy (DocExtractorError base)
│   ├── domain/
│   │   ├── interfaces.py            # ABCs: LLMClient, DocumentExtractionStrategy
│   │   ├── enumx/
│   │   │   ├── document_type.py     # DocumentType enum (cnh, aso, certificate)
│   │   │   └── llm_model.py         # LLMModel enum (gemini-pro, gemini-flash)
│   │   ├── dto/
│   │   │   ├── extract_request.py   # ExtractDocumentRequest
│   │   │   └── extract_response.py  # ExtractedDocument
│   │   └── models/
│   │       ├── cnh.py               # CNHData Pydantic model
│   │       └── certificate.py       # CertificateData Pydantic model
│   ├── services/
│   │   ├── factory.py               # ExtractorFactory (maps DocumentType → Strategy)
│   │   ├── orchestrator.py          # DocumentOrchestrator (main use-case coordinator)
│   │   └── strategies/
│   │       ├── cnh.py               # CNHExtractionStrategy
│   │       └── certificate.py       # CertificateExtractionStrategy
│   └── infra/
│       └── llm/
│           ├── gemini_client.py     # PydanticAILLMClient (implements LLMClient ABC)
│           └── model_factory.py     # ModelFactory (builds pydantic-ai Model instances)
└── frontend/                        # TypeScript — React SPA
    ├── index.html                   # Entry HTML (Vite SPA)
    ├── package.json                 # Dependencies & scripts
    ├── vite.config.ts               # Vite config (React plugin)
    ├── tsconfig.json                # TypeScript project references
    ├── tsconfig.app.json            # App-specific TS config (strict mode)
    ├── eslint.config.js             # ESLint flat config
    └── src/
        ├── main.tsx                 # React root (StrictMode)
        ├── App.tsx                  # Main component (form, state, submit logic)
        ├── api.ts                   # API client (fetch-based, talks to backend)
        ├── types.ts                 # TypeScript interfaces (DocumentTypeOption, LLMModelOption, ExtractedDocument)
        └── index.css                # Global styles (minimal, system-ui)
```

## Architecture & Design Patterns

The codebase must be **Object-Oriented** and follow **SOLID** principles. Contracts (Interfaces/ABCs) are mandatory.

### Backend Patterns

1. **Strategy Pattern**
   - Each document type (CNH, Certificate) has its own extraction class implementing `DocumentExtractionStrategy` ABC.
   - Each strategy owns its `SYSTEM_PROMPT` as a class constant and its associated Pydantic output model.
   - The API never handles extraction logic directly; it calls `.extract(file_content)`.

2. **Factory Pattern**
   - `ExtractorFactory` maps `DocumentType` enum → Strategy class via `_types_registry` dict.
   - Instantiates strategies with the injected `LLMClient`.

3. **Orchestrator Pattern**
   - `DocumentOrchestrator` is the single use-case entry point.
   - Flow: receives request → obtains strategy from factory → delegates extraction → returns result.

4. **Dependency Injection (FastAPI)**
   - Full DI chain in `api/dependencies.py`:
     `Settings → ModelFactory → PydanticAILLMClient → ExtractorFactory → DocumentOrchestrator`
   - Uses `typing.Annotated` with `Depends` throughout.
   - Routers are fully decoupled from concrete implementations.

5. **Adapters/Ports (Hexagonal Architecture)**
   - Domain code (`domain/`) has **zero** external library imports (no pydantic-ai, no google SDK).
   - `LLMClient` ABC is the port; `PydanticAILLMClient` in `infra/llm/` is the adapter.
   - `ModelFactory` abstracts provider-specific model construction (currently Google Gemini).

6. **Model Factory (LLM Provider Abstraction)**
   - `ModelFactory` builds `pydantic_ai.models.Model` instances from `LLMModel` enum members.
   - Provider builders are registered in `_BUILDERS` dict; adding a new provider requires only a new builder method.
   - Model identifiers are mapped in `core/config.py` via `MODEL_IDENTIFIERS`.

### Frontend Architecture
- **Single-Page Application** with vanilla React (no routing library).
- **API-driven UI**: document types and LLM models are fetched dynamically from the backend at startup (`GET /v1/document-types`, `GET /v1/llm-models`), so the frontend never hardcodes domain options.
- **Fetch-based API client** in `api.ts` with proper error handling (parses `detail` from JSON error responses).
- **No state management library**: uses React `useState` and `useEffect` hooks only (appropriate for current complexity).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/v1/extract` | Extract data from uploaded document (multipart: `file`, `document_type`, optional `llm_model`) |
| `GET` | `/v1/document-types` | List all supported document types with labels |
| `GET` | `/v1/llm-models` | List all available LLM models with labels |

### Extract Endpoint Details
- **Inputs:** `file: UploadFile`, `document_type: DocumentType` (form), `llm_model: LLMModel | None` (form, optional)
- **Flow:** Router → Orchestrator → Factory → Strategy → LLMClient → JSON Response
- **Response model:** `ExtractedDocument` with `document_type` and `data: dict[str, Any]`

## Currently Supported Document Types

| DocumentType Enum | Model | Strategy | Fields |
|---|---|---|---|
| `cnh` | `CNHData` | `CNHExtractionStrategy` | nome, numero_registro, cpf, data_validade |
| `certificate` | `CertificateData` | `CertificateExtractionStrategy` | nome, cpf, data |
| `aso` | *(registered in enum, no strategy yet)* | — | — |

## Currently Supported LLM Models

| LLMModel Enum | Provider Identifier | Label |
|---|---|---|
| `gemini-pro` | `gemini-3-pro-preview` | Gemini 3 Pro |
| `gemini-flash` | `gemini-3-flash-preview` | Gemini 3 Flash |

## Configuration

All backend environment variables use the `DOC_EXTRACTOR_` prefix (managed by `pydantic-settings`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `DOC_EXTRACTOR_GEMINI_API_KEY` | **Yes** | `""` | Google Gemini API key |
| `DOC_EXTRACTOR_DEFAULT_LLM_MODEL` | No | `gemini-pro` | Default LLM model (`LLMModel` enum value) |
| `DOC_EXTRACTOR_APP_NAME` | No | `Doc Extractor API` | Application name |
| `DOC_EXTRACTOR_ENVIRONMENT` | No | `development` | Environment (development, production) |
| `DOC_EXTRACTOR_LOG_LEVEL` | No | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

Frontend connects to `http://localhost:8000` (hardcoded in `api.ts`).

## Development Commands

### Prerequisites
- Python 3.12+
- `uv` package manager
- Node.js (for frontend)
- Docker & Docker Compose (optional)

### Backend — Local Development
```bash
# Install dependencies
uv sync

# Run in dev mode (hot reload)
uv run fastapi dev src/backend/main.py

# Run tests
uv run pytest
```

### Frontend — Local Development
```bash
cd src/frontend

# Install dependencies
npm install

# Run dev server (Vite, default port 5173)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### Docker
```bash
# Production build & run
docker compose up --build

# Development mode (with volume mount for hot reload)
docker compose --profile dev up --build
```

The production `Dockerfile` uses a **multi-stage build** (builder → slim runtime with non-root user).
The development `Dockerfile.dev` is a single-stage image with source mounted via volume.

## Coding Standards & Conventions

### Python (Backend)
- **Type Hints:** Mandatory for 100% of functions/methods.
- **Dependencies:** Use `typing.Annotated` with `Depends` in FastAPI endpoints.
- **No Any:** Avoid `typing.Any` unless strictly necessary (currently used only in `ExtractedDocument.data`).
- **Async:** All endpoint handlers and strategy `extract` methods are `async`.
- **ABCs over Protocols:** The project uses `abc.ABC` + `@abstractmethod` for contracts (`LLMClient`, `DocumentExtractionStrategy`).
- **Enum pattern:** Enums use `(str, Enum)` for JSON serialization compatibility.
- **Package organization:** Domain sub-packages use `__init__.py` re-exports with `__all__`.

### TypeScript (Frontend)
- **Strict mode:** TypeScript strict checks enabled (`strict: true`, `noUnusedLocals`, `noUnusedParameters`).
- **Explicit types:** Use `interface` for API response shapes; avoid `any`.
- **Functional components:** React components are pure functions with hooks.
- **Named exports:** Default export only for the root `App` component.

### Pydantic & LLM Guidelines
- **Field Descriptions:** Crucial for LLM structured extraction. Every field in domain models must have a `description` that guides the LLM.
  ```python
  class CNHData(BaseModel):
      numero_registro: str = Field(
          description="CNH registration number (Nº Registro), digits only, without dots or dashes."
      )
  ```

### Error Handling
- **No 500s:** Avoid internal server errors for predictable failures.
- **Domain Exception Hierarchy:**
  - `DocExtractorError` — base exception for all domain errors.
  - `DocumentUnreadableError` → mapped to HTTP 422.
  - `UnsupportedDocumentTypeError` → mapped to HTTP 400.
- Exception handlers are registered in `main.py` via `@app.exception_handler`.

### Prompt Engineering
- **Encapsulation:** System prompts must reside within the Strategy class as a `SYSTEM_PROMPT` class constant, never hardcoded in the method logic.
- **Strict extraction rules:** Prompts must instruct the LLM to extract only visible data, never infer or fabricate, and return empty strings for illegible fields.

## Extensibility Workflows

### Adding a New Document Type
1. **Create Model:** `class NovoDocumentoData(BaseModel)` in `domain/models/novo_documento.py` with `Field(description=...)` on every field.
2. **Re-export:** Add to `domain/models/__init__.py`.
3. **Add Enum Member:** Add to `DocumentType` enum in `domain/enumx/document_type.py`.
4. **Create Strategy:** `class NovoDocumentoExtractionStrategy(DocumentExtractionStrategy)` in `services/strategies/novo_documento.py` with its own `SYSTEM_PROMPT`.
5. **Register in Factory:** Add mapping in `ExtractorFactory._types_registry`.
6. **Add Label:** Add human-readable label in `routers/document_types.py` → `DOCUMENT_TYPE_LABELS`.

**Constraint:** Never modify the Router handler logic, Orchestrator, or frontend code when adding new types. The frontend dynamically fetches available types.

### Adding a New LLM Model
1. **Add Enum Member:** Add to `LLMModel` enum in `domain/enumx/llm_model.py`.
2. **Add Identifier:** Map in `core/config.py` → `MODEL_IDENTIFIERS`.
3. **Register Builder:** Add entry in `ModelFactory._BUILDERS` (may reuse existing builder for same provider).
4. **Add Label:** Add human-readable label in `routers/llm_models.py` → `LLM_MODEL_LABELS`.

### Adding a New LLM Provider (e.g., OpenAI, Anthropic)
1. Add a new private builder method in `ModelFactory` (e.g., `_build_openai`).
2. Register it in `ModelFactory._BUILDERS` for the corresponding `LLMModel` enum members.
3. Add any required API key settings to `core/config.py`.

## Key Implementation Details

### CORS
- CORS is enabled in `main.py` with `allow_origins=["*"]` (all origins, all methods, all headers) for development. Restrict in production.

### MIME Type Detection
- `PydanticAILLMClient._detect_mime_type()` infers file type from magic bytes (supports PDF, PNG, JPEG, WEBP; falls back to `application/octet-stream`).

### Pydantic AI Agent
- Each extraction call creates a fresh `Agent` instance with the target `output_type` (Pydantic model) and `system_prompt`.
- The document bytes are sent as `BinaryContent` with the detected MIME type.
- Structured output is enforced by pydantic-ai, guaranteeing Pydantic validation on the response.

## Notes for AI Assistant

- **Monorepo Context:** The project has two apps — `src/backend` (Python) and `src/frontend` (TypeScript/React). Changes to one may affect the other (e.g., API contract changes).
- **Backend Dependencies:** Use `uv add <package>` for adding Python packages. Never use `pip install` directly.
- **Frontend Dependencies:** Use `npm install <package>` from `src/frontend/`.
- **File Integrity:** Do not remove existing files unless instructed.
- **Security:** Never hardcode API keys; always refer to `core/config.py` and environment variables.
- **LLM Library:** The project uses **pydantic-ai** (not LangChain). Do not introduce LangChain imports.
- **Domain Purity:** The `domain/` package must never import from `infra/`, `services/`, or external LLM libraries. It defines only ABCs, enums, DTOs, and Pydantic models.
- **Frontend Autonomy:** The frontend discovers available document types and LLM models via API calls, so adding new types requires no frontend changes.
