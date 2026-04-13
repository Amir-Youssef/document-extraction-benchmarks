"""Type definitions for the experiment runner.

All dataclasses and type aliases used across the experiment modules.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GroundTruthEntry:
    """A single ground-truth record from the dataset JSON.

    Attributes:
        doc: Filename of the document (e.g. ``"arquivo.pdf"``).
        tipo: Document type string sent to the backend.
        tags: Free-form tags for filtering (e.g. ``["pdf", "escaneado"]``).
        respostas: Expected field→value mapping.
                   ────────────────────────────────────────────────────────
                   Os campos dentro de ``respostas`` variam por tipo de
                   documento.  Ao trocar o tipo de documento para um novo
                   experimento, ajuste **apenas o arquivo JSON do dataset**
                   (campo ``respostas`` de cada entrada em
                   ``ground_truth``).  Nenhuma alteração de código é
                   necessária — as métricas são calculadas dinamicamente
                   sobre qualquer conjunto de chaves presente aqui.
                   ────────────────────────────────────────────────────────
    """

    doc: str
    tipo: str
    tags: list[str]
    respostas: dict[str, str]


@dataclass(frozen=True)
class ExtractionResult:
    """Result of a single backend extraction call.

    Attributes:
        model: The ``llm_model`` identifier used.
        document_type: The ``document_type`` sent.
        doc_name: Filename that was sent.
        response_data: Parsed ``data`` dict from the backend response.
        latency_seconds: Wall-clock time of the HTTP call.
        success: Whether the call returned HTTP 200.
        error: Error message when ``success`` is False.
        repetition: 1-based repetition index.
    """

    model: str
    document_type: str
    doc_name: str
    response_data: dict[str, str]
    latency_seconds: float
    success: bool
    error: str
    repetition: int


@dataclass(frozen=True)
class FieldComparison:
    """Comparison of a single field between prediction and ground truth.

    Attributes:
        field_name: Name of the field.
        expected: Normalised ground-truth value.
        predicted: Normalised model value.
        match: Whether they are equal after normalisation.
    """

    field_name: str
    expected: str
    predicted: str
    match: bool
    levenshtein_similarity: float


@dataclass(frozen=True)
class DocumentEvaluation:
    """Evaluation result for one document / one model / one repetition.

    Attributes:
        doc_name: Filename.
        model: LLM model identifier.
        repetition: 1-based repetition index.
        field_comparisons: Per-field comparison results.
        precision: Precision for this document.
        recall: Recall for this document.
        f1: F1-score for this document.
        accuracy: Fraction of fields that matched.
        latency_seconds: Latency of this extraction.
    """

    doc_name: str
    model: str
    document_type: str
    repetition: int
    field_comparisons: list[FieldComparison]
    precision: float
    recall: float
    f1: float
    accuracy: float
    mean_levenshtein: float
    latency_seconds: float


@dataclass(frozen=True)
class ModelReport:
    """Aggregated report for a single model across the full dataset.

    Attributes:
        model: LLM model identifier.
        total_documents: Number of document evaluations.
        mean_latency: Average latency in seconds.
        mean_f1: Macro-average F1.
        mean_precision: Macro-average precision.
        mean_recall: Macro-average recall.
        mean_accuracy: Macro-average accuracy.
        document_evaluations: All individual evaluations.
    """

    model: str
    total_documents: int
    mean_latency: float
    mean_f1: float
    mean_precision: float
    mean_recall: float
    mean_accuracy: float
    mean_levenshtein: float
    document_evaluations: list[DocumentEvaluation] = field(default_factory=list)
