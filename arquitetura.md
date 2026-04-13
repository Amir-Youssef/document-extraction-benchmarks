# Arquitetura do Backend (Doc Extractor)

Este documento descreve a arquitetura **somente do backend**, destacando o fluxo principal de extração via endpoint e a forma como o projeto é facilmente extensível por estratégias.


## Endpoints do Backend

```mermaid
flowchart LR
    subgraph Endpoints
        E1[GET /health] -->|status| H1["{ status: ok }"]
        E2[GET /v1/document-types] -->|lista tipos| H2[Tipos suportados]
        E3[GET /v1/llm-models] -->|lista modelos| H3[Modelos LLM]
        E4[POST /v1/extract] -->|arquivo + tipo| H4[Documento extraído]
    end
```


## Visão Geral (Diagrama do Fluxo Principal)

```mermaid
flowchart LR
  A[Cliente] -->|POST /v1/extract<br/>file, document_type| B[API Router: extract.py]
  B --> C[DocumentOrchestrator]
  C -->|usa| E[DocumentExtractionStrategy]
  C --> D[ExtractorFactory]
  D -->|cria conforme DocumentType| S1[CNHExtractionStrategy]
  D -->|cria conforme DocumentType| S2[CertificateExtractionStrategy]
  D -->|cria conforme DocumentType| S3[ASOExtractionStrategy]
  S1 -. implementa .-> E
  S2 -. implementa .-> E
  S3 -. implementa .-> E
  S1 ===|Extrai informações| D1
  S2 ===|Extrai informações| D2
  S3 ===|Extrai informações| D3
  C --> B
  B --> J[Resposta JSON: ExtractedDocument]

  subgraph API
    B
  end

  subgraph Aplicação
    C
    D
    E
  end

  subgraph "Strategies (Implementações)"
    S1
    S2
    S3
  end

  subgraph "Domain (Tipos de documento)"
    D1[CNH]
    D2[Certificate]
    D3[ASO]
  end
```

## Extensibilidade (Como adicionar um novo tipo de documento)

A arquitetura segue Strategy + Factory, permitindo adicionar novos tipos sem mudar o fluxo principal. Passos resumidos:

```mermaid
flowchart TB
    N1[Criar Pydantic Model<br/>domain/models/novo_tipo.py] --> N2[Adicionar no enum<br/>DocumentType]
    N2 --> N3[Criar Strategy<br/>services/strategies/novo_tipo.py]
    N3 --> N4[Registrar no ExtractorFactory]
    N4 --> N5[Adicionar label em document_types.py]
```

**Resultado:** o endpoint `POST /v1/extract` continua o mesmo, mas passa a suportar o novo tipo automaticamente.