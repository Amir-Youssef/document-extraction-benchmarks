# Doc Extractor

Aplicação full-stack para upload de documentos (PDFs ou imagens), identificação de tipo e extração de dados estruturados usando LLMs (Google Gemini via Pydantic AI).

Envie uma foto de um documento brasileiro → receba um JSON validado com os campos extraídos.

```
┌──────────┐                             ┌────────────────┐      Gemini       ┌──────────┐
│ Frontend │     POST /v1/extract        │    Backend     │  ──────────────▶  │  Google  │
│  (React) │  ───────────────────────▶   │   (FastAPI)    │   structured out  │  Gemini  │
└──────────┘    file + document_type     └────────────────┘                   └──────────┘
                  + llm_model (opt)             │
                                                ▼
                                         JSON estruturado
                                       (Pydantic validated)
```

---

## Tecnologias Utilizadas

### Backend

| Tecnologia | Papel |
|---|---|
| **Python 3.12+** | Linguagem principal |
| **FastAPI** | Framework web (endpoints, DI, validação, CORS) |
| **Pydantic v2** | Validação de dados e modelos de domínio |
| **Pydantic AI** | Orquestração de chamadas ao LLM (provider-agnostic) |
| **Google Gemini** | LLM multimodal (visão + texto) via `pydantic-ai[google]` |
| **pydantic-settings** | Gerenciamento de configuração via variáveis de ambiente |
| **uv** | Gerenciamento de dependências e virtualenv |
| **Docker** | Containerização (multi-stage production + dev) |

### Frontend

| Tecnologia | Papel |
|---|---|
| **TypeScript** | Linguagem (strict mode) |
| **React 19** | Framework de UI (functional components, hooks) |
| **Vite 7** | Build tool e dev server |
| **ESLint 9** | Linting com `typescript-eslint`, `react-hooks`, `react-refresh` |

---

## Arquitetura

O sistema segue princípios **SOLID** com design patterns centrais:

| Pattern | Classe | Responsabilidade |
|---|---|---|
| **Strategy** | `DocumentExtractionStrategy` | Cada tipo de documento tem sua própria estratégia de extração |
| **Factory** | `ExtractorFactory` | Mapeia `DocumentType` → Strategy e instancia com o `LLMClient` |
| **Orchestrator** | `DocumentOrchestrator` | Coordena o fluxo: recebe request → obtém strategy → executa → retorna |
| **Model Factory** | `ModelFactory` | Abstrai a construção de modelos LLM por provider |

### Separação de camadas (Backend)

```
api/          → Camada HTTP (FastAPI). Routers finos, DI, validação de entrada.
domain/       → Camada pura. Modelos Pydantic, enums, interfaces (ABC). Zero dependências externas.
services/     → Lógica de negócio. Factory, Orchestrator, Strategies concretas.
infra/        → Adapters de I/O. Implementação do LLMClient usando Pydantic AI + Gemini.
core/         → Configuração global. Settings, logging, exceções de domínio.
```

O domínio **nunca** importa FastAPI, Pydantic AI ou qualquer biblioteca de infraestrutura. A comunicação com LLMs é feita exclusivamente através da interface `LLMClient` (ABC), implementada por `PydanticAILLMClient` na camada de infraestrutura.

### Frontend

- **SPA** com React puro (sem routing library).
- **UI API-driven**: tipos de documento e modelos LLM são carregados dinamicamente do backend (`GET /v1/document-types`, `GET /v1/llm-models`), então o frontend **nunca** hardcoda opções de domínio.
- **API client** fetch-based em `api.ts` com tratamento de erros (parse de `detail` da resposta JSON).

---

## Estrutura de Pastas

O projeto é um **monorepo** com duas aplicações independentes em `src/`:

```
src/
├── backend/                         # Python — FastAPI REST API
│   ├── main.py                      # App factory, CORS, exception handlers, router registration
│   ├── api/
│   │   ├── dependencies.py          # Cadeia completa de DI (Settings → ModelFactory → LLMClient → Factory → Orchestrator)
│   │   └── routers/
│   │       ├── health.py            # GET /health
│   │       ├── extract.py           # POST /v1/extract
│   │       ├── document_types.py    # GET /v1/document-types
│   │       └── llm_models.py        # GET /v1/llm-models
│   ├── core/
│   │   ├── config.py                # Settings (pydantic-settings), MODEL_IDENTIFIERS mapping
│   │   ├── logging.py               # Logging estruturado
│   │   └── exceptions.py            # Hierarquia de exceções de domínio (DocExtractorError base)
│   ├── domain/
│   │   ├── interfaces.py            # ABCs: LLMClient, DocumentExtractionStrategy
│   │   ├── enumx/
│   │   │   ├── document_type.py     # DocumentType enum (cnh, aso, certificate)
│   │   │   └── llm_model.py         # LLMModel enum (gemini-pro, gemini-flash)
│   │   ├── dto/
│   │   │   ├── extract_request.py   # ExtractDocumentRequest
│   │   │   └── extract_response.py  # ExtractedDocument
│   │   └── models/
│   │       ├── cnh.py               # CNHData (modelo Pydantic)
│   │       └── certificate.py       # CertificateData (modelo Pydantic)
│   ├── services/
│   │   ├── factory.py               # ExtractorFactory
│   │   ├── orchestrator.py          # DocumentOrchestrator
│   │   └── strategies/
│   │       ├── cnh.py               # CNHExtractionStrategy
│   │       └── certificate.py       # CertificateExtractionStrategy
│   └── infra/
│       └── llm/
│           ├── gemini_client.py     # PydanticAILLMClient (adapter Pydantic AI)
│           └── model_factory.py     # ModelFactory (constrói instâncias de Model por provider)
└── frontend/                        # TypeScript — React SPA
    ├── index.html                   # Entry HTML (Vite SPA)
    ├── package.json                 # Dependências & scripts
    ├── vite.config.ts               # Config Vite (plugin React)
    ├── tsconfig.json                # Project references TypeScript
    ├── tsconfig.app.json            # Config TS da app (strict mode)
    ├── eslint.config.js             # ESLint flat config
    └── src/
        ├── main.tsx                 # React root (StrictMode)
        ├── App.tsx                  # Componente principal (form, state, submit)
        ├── api.ts                   # API client (fetch-based, conecta ao backend)
        ├── types.ts                 # Interfaces TypeScript (DocumentTypeOption, LLMModelOption, ExtractedDocument)
        └── index.css                # Estilos globais (minimal, system-ui)
```

---

## Pré-requisitos

- **Python** 3.12 ou superior
- **uv** ([docs.astral.sh/uv](https://docs.astral.sh/uv/)) — gerenciador de pacotes Python
- **Node.js** 18+ e **npm** — para o frontend
- **Chave de API do Google Gemini** ([aistudio.google.com](https://aistudio.google.com/))
- **Docker** e **Docker Compose** (opcional, para execução containerizada)

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd doc-extractor
```

### 2. Configurar variáveis de ambiente

Todas as variáveis de ambiente do backend usam o prefixo `DOC_EXTRACTOR_`.

Crie um arquivo `.env` na **raiz do projeto**:

```env
DOC_EXTRACTOR_GEMINI_API_KEY=sua-chave-aqui
DOC_EXTRACTOR_DEFAULT_LLM_MODEL=gemini-pro
DOC_EXTRACTOR_ENVIRONMENT=development
DOC_EXTRACTOR_LOG_LEVEL=INFO
```

> ⚠️ **Nunca** commite chaves de API. O `.env` já está no `.gitignore`.

#### Variáveis disponíveis

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `DOC_EXTRACTOR_GEMINI_API_KEY` | **Sim** | `""` | Chave de API do Google Gemini |
| `DOC_EXTRACTOR_DEFAULT_LLM_MODEL` | Não | `gemini-pro` | Modelo LLM padrão (`gemini-pro` ou `gemini-flash`) |
| `DOC_EXTRACTOR_APP_NAME` | Não | `Doc Extractor API` | Nome da aplicação |
| `DOC_EXTRACTOR_ENVIRONMENT` | Não | `development` | Ambiente de execução |
| `DOC_EXTRACTOR_LOG_LEVEL` | Não | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### 3. Instalar dependências

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

## Como rodar localmente

### Backend

```bash
# Subir a API em modo desenvolvimento (hot reload na porta 8000)
uv run fastapi dev src/backend/main.py

# Verificar que está funcionando
curl http://localhost:8000/health
# {"status":"ok"}
```

A documentação interativa (Swagger) estará disponível em: http://localhost:8000/docs

### Frontend

Em outro terminal:

```bash
cd src/frontend
npm run dev
```

O frontend estará disponível em: http://localhost:5173

> O frontend conecta ao backend em `http://localhost:8000` (hardcoded em `api.ts`). Certifique-se de que o backend está rodando antes de usar o frontend.

---

## Como rodar com Docker

O Docker Compose possui dois serviços: **produção** e **desenvolvimento**.

### Produção

O Dockerfile de produção usa um **multi-stage build** (builder → slim runtime com usuário não-root).

```bash
# Build e subir
docker compose up --build

# Validar
curl http://localhost:8000/health
```

### Desenvolvimento

O Dockerfile de desenvolvimento monta o código fonte via volume para hot reload.

```bash
# Build e subir com profile dev
docker compose --profile dev up --build
```

Porta padrão exposta: **8000**.

> **Nota:** Os Dockerfiles atuais cobrem apenas o backend. O frontend deve ser executado localmente com `npm run dev` durante o desenvolvimento.

---

## Endpoints da API

| Método | Path | Descrição |
|---|---|---|
| `GET` | `/health` | Health check — retorna `{"status": "ok"}` |
| `POST` | `/v1/extract` | Extrai dados de um documento enviado |
| `GET` | `/v1/document-types` | Lista todos os tipos de documento suportados |
| `GET` | `/v1/llm-models` | Lista todos os modelos LLM disponíveis |

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### Listar tipos de documento

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

### Listar modelos LLM

```bash
curl http://localhost:8000/v1/llm-models
```

```json
[
  {"value": "gemini-pro", "label": "Gemini 3 Pro"},
  {"value": "gemini-flash", "label": "Gemini 3 Flash"}
]
```

### Extrair dados de documento

```
POST /v1/extract
Content-Type: multipart/form-data
```

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `file` | `UploadFile` | Sim | Arquivo do documento (PDF, PNG, JPEG, WEBP) |
| `document_type` | `string` | Sim | Tipo do documento: `cnh`, `aso`, `certificate` |
| `llm_model` | `string` | Não | Modelo LLM: `gemini-pro` ou `gemini-flash` (usa o padrão se omitido) |

#### Exemplo com curl

```bash
curl -X POST http://localhost:8000/v1/extract \
  -F "file=@/caminho/para/cnh.pdf" \
  -F "document_type=cnh" \
  -F "llm_model=gemini-flash"
```

#### Exemplo de resposta (CNH)

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

#### Exemplo de resposta (Certificate)

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

## Tipos de documento suportados

| Tipo | Enum | Modelo Pydantic | Strategy | Campos extraídos |
|---|---|---|---|---|
| CNH | `cnh` | `CNHData` | `CNHExtractionStrategy` | `nome`, `numero_registro`, `cpf`, `data_validade` |
| Certificado | `certificate` | `CertificateData` | `CertificateExtractionStrategy` | `nome`, `cpf`, `data` |
| ASO | `aso` | *(sem strategy ainda)* | — | — |

## Modelos LLM disponíveis

| Enum | Identificador do Provider | Label |
|---|---|---|
| `gemini-pro` | `gemini-3-pro-preview` | Gemini 3 Pro |
| `gemini-flash` | `gemini-3-flash-preview` | Gemini 3 Flash |

---

## Como contribuir

### Adicionando um novo tipo de documento

O sistema foi projetado para que adicionar um novo tipo de documento **não exija alterar endpoints, Orchestrator, nem o frontend**. São 6 passos:

#### 1. Criar o modelo Pydantic

Arquivo: `src/backend/domain/models/novo_documento.py`

> Cada field **deve** ter `description` — é o que guia o LLM na extração.

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

#### 2. Re-exportar no `__init__.py`

Em `src/backend/domain/models/__init__.py`:

```python
from backend.domain.models.novo_documento import NovoDocumentoData

__all__ = [
    "CNHData",
    "CertificateData",
    "NovoDocumentoData",  # novo
]
```

#### 3. Adicionar membro ao enum `DocumentType`

Em `src/backend/domain/enumx/document_type.py`:

```python
class DocumentType(str, Enum):
    CNH = "cnh"
    ASO = "aso"
    CERTIFICATE = "certificate"
    NOVO_DOCUMENTO = "novo_documento"  # novo
```

#### 4. Criar a Strategy

Arquivo: `src/backend/services/strategies/novo_documento.py`

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

#### 5. Registrar na Factory

Em `src/backend/services/factory.py`, adicionar ao `_types_registry`:

```python
from backend.services.strategies.novo_documento import NovoDocumentoExtractionStrategy

# Dentro do __init__:
self._types_registry = {
    DocumentType.CNH: CNHExtractionStrategy,
    DocumentType.CERTIFICATE: CertificateExtractionStrategy,
    DocumentType.NOVO_DOCUMENTO: NovoDocumentoExtractionStrategy,  # novo
}
```

#### 6. Adicionar label legível

Em `src/backend/api/routers/document_types.py`, adicionar ao `DOCUMENT_TYPE_LABELS`:

```python
DOCUMENT_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.CNH: "Carteira Nacional de Habilitação",
    DocumentType.ASO: "Atestado de Saúde Ocupacional",
    DocumentType.CERTIFICATE: "Certificado",
    DocumentType.NOVO_DOCUMENTO: "Novo Documento",  # novo
}
```

> **O endpoint `POST /v1/extract`, o Orchestrator e o frontend não precisam ser alterados.** O novo tipo será automaticamente disponível na UI e na API.

---

### Adicionando um novo modelo LLM (mesmo provider)

Para adicionar um novo modelo do Google Gemini (ou qualquer provider já existente):

1. **Enum:** Adicionar membro em `src/backend/domain/enumx/llm_model.py`.
2. **Identificador:** Mapear em `src/backend/core/config.py` → `MODEL_IDENTIFIERS`.
3. **Builder:** Registrar em `ModelFactory._BUILDERS` em `src/backend/infra/llm/model_factory.py` (pode reusar builder existente).
4. **Label:** Adicionar label legível em `src/backend/api/routers/llm_models.py` → `LLM_MODEL_LABELS`.

### Adicionando um novo provider LLM (e.g., OpenAI, Anthropic)

1. Adicionar um novo método builder privado em `ModelFactory` (e.g., `_build_openai`).
2. Registrar no `ModelFactory._BUILDERS` para os membros de `LLMModel` correspondentes.
3. Adicionar as configurações necessárias (API keys, etc.) em `src/backend/core/config.py`.

---

## Erros comuns e como resolver

### API Key inválida ou ausente

```
ValidationError: API key required for Gemini Developer API
```

**Solução:** Defina a variável de ambiente `DOC_EXTRACTOR_GEMINI_API_KEY` com uma chave válida no arquivo `.env`.

### Tipo de documento sem strategy

```json
{"detail": "No extraction strategy registered for document type: 'aso'"}
```

**Solução:** O tipo `aso` está registrado no enum mas ainda não possui uma strategy implementada. Siga o guia "Adicionando um novo tipo de documento" para implementá-lo.

### Frontend não conecta ao backend

Se o frontend exibe "Falha ao carregar tipos de documento", verifique:
1. O backend está rodando na porta 8000.
2. O CORS está habilitado (já está por padrão em desenvolvimento).
3. O `BASE_URL` em `src/frontend/src/api.ts` aponta para `http://localhost:8000`.

### Tipo de documento não suportado

```json
{"detail": "No extraction strategy registered for document type: 'aso'"}
```

**Causa:** O `DocumentType` existe no enum mas não tem Strategy registrada na Factory.  
**Solução:** Implemente a Strategy correspondente e registre na Factory.

### Erro de validação Pydantic (422)

```json
{"detail": [{"type": "enum", "msg": "Input should be 'cnh', 'aso' or 'certificate'"}]}
```

**Causa:** O valor enviado em `document_type` não corresponde a nenhum membro do enum.  
**Solução:** Use um dos valores aceitos: `cnh`, `aso`, `certificate`.

### Documento ilegível

```json
{"detail": "Document could not be read or parsed"}
```

**Causa:** O arquivo enviado está corrompido, vazio ou em formato não suportado.  
**Solução:** Verifique o arquivo e envie um PDF ou imagem legível (PNG, JPEG, WEBP).

---

## Observações finais

### Boas práticas aplicadas

- **SOLID** — Cada classe tem responsabilidade única; dependências são injetadas via interfaces
- **Type hints em 100%** das funções e métodos
- **Domínio puro** — Modelos e interfaces sem dependências de infraestrutura
- **Structured Output** — O LLM retorna diretamente um objeto Pydantic validado, nunca JSON cru


Implementar caching do LLM client (singleton na DI)