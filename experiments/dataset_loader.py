"""Dataset loader — reads the ground-truth JSON and pairs it with files.

Expected dataset layout::

    <dataset_root>/
    ├── <tipo_a>/
    │   ├── ground_truth.json
    │   ├── doc1.pdf
    │   └── doc2.png
    └── <tipo_b>/
        ├── ground_truth.json
        └── doc3.pdf

The JSON file **must** follow this schema::

    {
      "ground_truth": [
        {
          "doc": "doc1.pdf",
          "tipo": "arrais",
          "tags": ["pdf", "escaneado"],
          "respostas": {
              "campo1": "valor1",
              "campo2": "valor2"
          }
        }
      ]
    }

────────────────────────────────────────────────────────────────────
ONDE AJUSTAR AO TROCAR O TIPO DE DOCUMENTO:

Nenhuma alteração de código é necessária.  Os campos esperados são
definidos **exclusivamente** no JSON do dataset, dentro de cada
objeto ``respostas``.  Para um novo tipo de documento, basta:

1. Criar uma nova pasta em ``<dataset_root>/<novo_tipo>/``
2. Colocar os arquivos (PDFs / imagens)
3. Criar ``ground_truth.json`` com os campos corretos em ``respostas``

As métricas são calculadas dinamicamente sobre qualquer conjunto de
chaves presente em ``respostas``.
────────────────────────────────────────────────────────────────────
"""

import json
from pathlib import Path

from experiments.experiment_types import GroundTruthEntry


def load_ground_truth(json_path: Path) -> list[GroundTruthEntry]:
    """Parse a ``ground_truth.json`` file into typed entries.

    Args:
        json_path: Path to the JSON file.

    Returns:
        List of :class:`GroundTruthEntry` instances.

    Raises:
        FileNotFoundError: If *json_path* does not exist.
        KeyError: If required keys are missing in the JSON.
    """
    with open(json_path, encoding="utf-8") as fh:
        raw: dict[str, list[dict[str, object]]] = json.load(fh)

    # Suporta tanto "ground_truth" (underscore) quanto "ground-truth" (hífen)
    data = raw.get("ground_truth") or raw.get("ground-truth")
    if data is None:
        return []

    entries: list[GroundTruthEntry] = []
    for item in data:
        # Tenta pegar 'respostas' ou 'resposta' (caso do arquivo de epi)
        respostas = item.get("respostas") or item.get("resposta")
        
        # Ignora entradas que não possuem os campos obrigatórios (como metadados ou erros)
        if not all(key in item for key in ["doc", "tipo"]) or respostas is None:
            continue

        # respostas pode ser um dict (1 resultado) ou uma list de dicts
        # (vários resultados para o mesmo documento, ex.: múltiplos crachás).
        # Expande cada item da lista em uma entrada separada.
        respostas_list = respostas if isinstance(respostas, list) else [respostas]
        for resp in respostas_list:
            if not isinstance(resp, dict):
                continue
            entry = GroundTruthEntry(
                doc=str(item["doc"]),
                tipo=str(item["tipo"]),
                tags=[str(t) for t in item.get("tags", [])],  # type: ignore[union-attr]
                respostas={str(k): str(v) for k, v in resp.items()},
            )
            entries.append(entry)
    return entries


def discover_dataset(dataset_root: Path) -> dict[str, list[GroundTruthEntry]]:
    """Walk *dataset_root* and discover all document types + entries.

    Each immediate subdirectory of *dataset_root* is treated as a
    document-type folder.  The folder must contain a
    ``ground_truth.json`` file.

    Args:
        dataset_root: Root directory of the dataset.

    Returns:
        Mapping of folder name → list of ground-truth entries.
    """
    result: dict[str, list[GroundTruthEntry]] = {}
    for child in sorted(dataset_root.iterdir()):
        if not child.is_dir():
            continue
        gt_file = child / "ground_truth.json"
        if not gt_file.exists():
            continue
        entries = load_ground_truth(gt_file)
        result[child.name] = entries
    return result


def resolve_file_path(dataset_root: Path, folder_name: str, doc_name: str) -> Path:
    """Build the absolute path to a document file.

    Args:
        dataset_root: Root directory of the dataset.
        folder_name: Name of the type sub-folder.
        doc_name: Filename from the ground-truth entry.

    Returns:
        Resolved :class:`Path`.

    Raises:
        FileNotFoundError: If the file does not exist on disk.
    """
    path = dataset_root / folder_name / doc_name
    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {path}")
    return path
