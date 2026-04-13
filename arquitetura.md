# Backend Architecture (Doc Extractor)

This document describes the **backend architecture only**, highlighting the main extraction flow via endpoint and how the project is easily extensible through strategies.


## Backend Endpoints

```mermaid
flowchart LR
    subgraph Endpoints
        E1[GET /health] -->|status| H1["{ status: ok }"]
        E2[GET /v1/document-types] -->|list types| H2[Supported types]
        E3[GET /v1/llm-models] -->|list models| H3[LLM models]
        E4[POST /v1/extract] -->|file + type| H4[Extracted document]
    end
```


## Overview (Main Flow Diagram)

```mermaid
flowchart LR
  A[Client] -->|POST /v1/extract<br/>file, document_type| B[API Router: extract.py]
  B --> C[DocumentOrchestrator]
  C -->|uses| E[DocumentExtractionStrategy]
  C --> D[ExtractorFactory]
  D -->|creates according to DocumentType| S1[CNHExtractionStrategy]
  D -->|creates according to DocumentType| S2[CertificateExtractionStrategy]
  D -->|creates according to DocumentType| S3[ASOExtractionStrategy]
  S1 -. implements .-> E
  S2 -. implements .-> E
  S3 -. implements .-> E
  S1 ===|Extracts information| D1
  S2 ===|Extracts information| D2
  S3 ===|Extracts information| D3
  C --> B
  B --> J[JSON Response: ExtractedDocument]

  subgraph API
    B
  end

  subgraph Application
    C
    D
    E
  end

  subgraph "Strategies (Implementations)"
    S1
    S2
    S3
  end

  subgraph "Domain (Document types)"
    D1[CNH]
    D2[Certificate]
    D3[ASO]
  end
```

## Extensibility (How to add a new document type)

The architecture follows Strategy + Factory, allowing new types to be added without changing the main flow. Summary steps:

```mermaid
flowchart TB
    N1[Create Pydantic Model<br/>domain/models/new_type.py] --> N2[Add to enum<br/>DocumentType]
    N2 --> N3[Create Strategy<br/>services/strategies/new_type.py]
    N3 --> N4[Register in ExtractorFactory]
    N4 --> N5[Add label in document_types.py]
```

**Result:** the `POST /v1/extract` endpoint remains the same, but now supports the new type automatically.