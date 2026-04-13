"""Configuração do experimento — mapeamento de tipos e consulta ao backend.

Este módulo centraliza:

1. O mapeamento entre tipos de documento do **dataset** e tipos aceitos
   pelo **backend**.
2. Funções para consultar os endpoints ``/v1/llm-models`` e
   ``/v1/document-types`` do backend em tempo de execução.

────────────────────────────────────────────────────────────────────
ONDE AJUSTAR AO ADICIONAR UM NOVO TIPO DE DOCUMENTO NO DATASET:

Edite **apenas** o dicionário ``DATASET_TYPE_TO_BACKEND_TYPE`` abaixo.

A chave é o valor de ``tipo`` que aparece no ``ground_truth.json``
do dataset.  O valor é o ``document_type`` aceito pelo backend
(conforme retornado por ``GET /v1/document-types``).

Múltiplas chaves podem apontar para o mesmo valor do backend.
────────────────────────────────────────────────────────────────────
"""

import sys

import httpx


# ┌──────────────────────────────────────────────────────────────────┐
# │  MAPEAMENTO: tipo do dataset  →  document_type do backend       │
# │                                                                  │
# │  Adicione novas linhas aqui sempre que o dataset contiver um     │
# │  tipo que não existe como enum no backend.                       │
# │                                                                  │
# │  Exemplo:                                                        │
# │      "nr10"               → "certificate"                        │
# │      "nr10-sep"           → "certificate"                        │
# │      "resgate-afogados"   → "certificate"                        │
# │      "carteira-arrais"    → "certificate"                        │
# │      "carteira-marinheiro"→ "certificate"                        │
# │      "seguro-vida"        → "certificate"                        │
# │                                                                  │
# │  Se a chave for igual ao valor do backend, ela é opcional mas    │
# │  recomendada para deixar explícito.                              │
# └──────────────────────────────────────────────────────────────────┘
DATASET_TYPE_TO_BACKEND_TYPE: dict[str, str] = {
    # Mapeamentos identidade (chave == valor no backend)
    "cnh": "cnh",
    "aso": "aso",
    "epi": "epi",
    "ltcat": "ltcat",
    "pgr": "pgr",
    "pcmso": "pcmso",
    "nr10": "nr10",
    "nr35": "nr35",
    "nr12": "nr12",
    "afogados": "afogados",
    "arrais": "arrais",
    "marinheiro": "marinheiro",
    "seguro": "seguro",
    "certificate": "certificate",

    # Mapeamentos de tipos do dataset (com variações de nome/case/espaços) para o backend
    "Ficha de Registro": "ficha_registro",
    "NR12": "nr12",
    "NR35": "nr35",
    "nr 35": "nr35",
    "LTCAT": "ltcat",
    "PGR": "pgr",
    "nr10-sep": "nr10sep",
    "resgate-afogados": "afogados",
    "carteira-arrais": "arrais",
    "carteira-marinheiro": "marinheiro",
    "seguro-vida": "seguro",
}


def resolve_backend_type(dataset_type: str) -> str:
    """Converte um tipo do dataset para o ``document_type`` do backend.

    Procura primeiro no :data:`DATASET_TYPE_TO_BACKEND_TYPE`.  Se não
    encontrar, retorna o próprio valor (assume que é um tipo válido do
    backend).

    Args:
        dataset_type: Valor de ``tipo`` presente no ``ground_truth.json``.

    Returns:
        O ``document_type`` a ser enviado ao backend.
    """
    return DATASET_TYPE_TO_BACKEND_TYPE.get(dataset_type, dataset_type)


def fetch_available_models(backend_url: str) -> list[str]:
    """Consulta ``GET /v1/llm-models`` e retorna os ``value`` disponíveis.

    Args:
        backend_url: URL base do backend (ex: ``http://localhost:8000``).

    Returns:
        Lista de identificadores de modelo (ex: ``["gemini-pro", "gemini-flash"]``).
    """
    url = f"{backend_url.rstrip('/')}/v1/llm-models"
    try:
        response = httpx.get(url, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[ERROR] Falha ao consultar modelos em {url}: {exc}", file=sys.stderr)
        sys.exit(1)

    data: list[dict[str, str]] = response.json()
    models = [item["value"] for item in data]
    if not models:
        print("[ERROR] Nenhum modelo retornado pelo backend.", file=sys.stderr)
        sys.exit(1)
    return models


def fetch_available_document_types(backend_url: str) -> list[str]:
    """Consulta ``GET /v1/document-types`` e retorna os ``value`` disponíveis.

    Args:
        backend_url: URL base do backend.

    Returns:
        Lista de tipos de documento aceitos pelo backend.
    """
    url = f"{backend_url.rstrip('/')}/v1/document-types"
    try:
        response = httpx.get(url, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[ERROR] Falha ao consultar tipos de documento em {url}: {exc}", file=sys.stderr)
        sys.exit(1)

    data: list[dict[str, str]] = response.json()
    return [item["value"] for item in data]


def validate_type_mapping(backend_url: str, dataset_types: set[str]) -> None:
    """Valida que todos os tipos do dataset mapeiam para tipos válidos do backend.

    Imprime warnings para tipos sem mapeamento explícito e erros para
    tipos que não existem no backend.

    Args:
        backend_url: URL base do backend.
        dataset_types: Conjunto de ``tipo`` encontrados no dataset.
    """
    backend_types = set(fetch_available_document_types(backend_url))

    for dt in sorted(dataset_types):
        resolved = resolve_backend_type(dt)
        if dt not in DATASET_TYPE_TO_BACKEND_TYPE:
            print(
                f"[WARN] Tipo '{dt}' do dataset não tem mapeamento explícito "
                f"em DATASET_TYPE_TO_BACKEND_TYPE. Usando '{resolved}' diretamente.",
                file=sys.stderr,
            )
        if resolved not in backend_types:
            print(
                f"[ERROR] Tipo '{dt}' mapeia para '{resolved}', "
                f"mas '{resolved}' não é um tipo válido no backend. "
                f"Tipos válidos: {sorted(backend_types)}",
                file=sys.stderr,
            )
            sys.exit(1)
