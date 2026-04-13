"""Evaluator — sends documents to the backend and evaluates responses.

This module is the bridge between the dataset, the HTTP API and the
metrics layer.  It never imports anything from the product codebase.
"""

import time
from pathlib import Path

import httpx

from experiments.config import resolve_backend_type
from experiments import dataset_loader
from experiments.dataset_loader import resolve_file_path
from experiments.metrics import (
    accuracy,
    compute_field_matches,
    levenshtein_similarity,
    mean_levenshtein_similarity,
    normalise,
    precision_recall_f1,
)
from experiments.experiment_types import (
    DocumentEvaluation,
    ExtractionResult,
    FieldComparison,
    GroundTruthEntry,
    ModelReport,
)


def _send_extraction_request(
    client: httpx.Client,
    backend_url: str,
    file_path: Path,
    document_type: str,
    llm_model: str,
) -> tuple[dict[str, str], float, bool, str]:
    """POST a file to the backend ``/v1/extract`` endpoint.

    Args:
        client: Reusable httpx client.
        backend_url: Base URL of the backend (e.g. ``http://localhost:8000``).
        file_path: Absolute path to the document file.
        document_type: Value for the ``document_type`` form field.
        llm_model: Value for the ``llm_model`` form field.

    Returns:
        ``(response_data, latency_seconds, success, error_message)``
    """
    url = f"{backend_url.rstrip('/')}/v1/extract"
    with open(file_path, "rb") as fh:
        files = {"file": (file_path.name, fh)}
        data = {"document_type": document_type, "llm_model": llm_model}

        start = time.perf_counter()
        try:
            response = client.post(url, files=files, data=data, timeout=120.0)
            elapsed = time.perf_counter() - start
        except httpx.HTTPError as exc:
            elapsed = time.perf_counter() - start
            return {}, elapsed, False, str(exc)

    if response.status_code == 200:
        body: dict[str, object] = response.json()
        response_data: dict[str, str] = {
            str(k): str(v) for k, v in body.get("data", {}).items()  # type: ignore[union-attr]
        }
        return response_data, elapsed, True, ""

    error_detail = response.text
    try:
        error_body: dict[str, object] = response.json()
        if "detail" in error_body:
            error_detail = str(error_body["detail"])
    except Exception:
        pass
    return {}, elapsed, False, error_detail


def extract_single(
    client: httpx.Client,
    backend_url: str,
    dataset_root: Path,
    folder_name: str,
    entry: GroundTruthEntry,
    llm_model: str,
    repetition: int,
) -> ExtractionResult:
    """Run extraction for a single document and return the raw result.

    Args:
        client: httpx client instance.
        backend_url: Backend base URL.
        dataset_root: Root of the dataset directory.
        folder_name: Sub-folder name inside dataset root.
        entry: Ground-truth entry describing the document.
        llm_model: LLM model identifier.
        repetition: 1-based repetition index.

    Returns:
        :class:`ExtractionResult` with all fields populated.
    """
    file_path = resolve_file_path(dataset_root, folder_name, entry.doc)
    backend_type = resolve_backend_type(entry.tipo)
    response_data, latency, success, error = _send_extraction_request(
        client=client,
        backend_url=backend_url,
        file_path=file_path,
        document_type=backend_type,
        llm_model=llm_model,
    )
    return ExtractionResult(
        model=llm_model,
        document_type=entry.tipo,
        doc_name=entry.doc,
        response_data=response_data,
        latency_seconds=latency,
        success=success,
        error=error,
        repetition=repetition,
    )


def evaluate_single(
    result: ExtractionResult,
    entry: GroundTruthEntry,
) -> DocumentEvaluation:
    """Evaluate a single extraction result against ground truth.

    Args:
        result: Output of :func:`extract_single`.
        entry: Corresponding ground-truth entry.

    Returns:
        :class:`DocumentEvaluation` with per-field comparisons and scores.
    """
    if not result.success:
        return DocumentEvaluation(
            doc_name=result.doc_name,
            model=result.model,
            document_type=result.document_type,
            repetition=result.repetition,
            field_comparisons=[],
            precision=0.0,
            recall=0.0,
            f1=0.0,
            accuracy=0.0,
            mean_levenshtein=0.0,
            latency_seconds=result.latency_seconds,
        )

    field_matches = compute_field_matches(entry.respostas, result.response_data)
    comparisons = [
        FieldComparison(
            field_name=name,
            expected=exp,
            predicted=pred,
            match=match,
            levenshtein_similarity=levenshtein_similarity(exp, pred),
        )
        for name, exp, pred, match in field_matches
    ]
    prec, rec, f1_score = precision_recall_f1(entry.respostas, result.response_data)
    acc = accuracy(entry.respostas, result.response_data)
    mean_lev = mean_levenshtein_similarity(entry.respostas, result.response_data)

    return DocumentEvaluation(
        doc_name=result.doc_name,
        model=result.model,
        document_type=result.document_type,
        repetition=result.repetition,
        field_comparisons=comparisons,
        precision=prec,
        recall=rec,
        f1=f1_score,
        accuracy=acc,
        mean_levenshtein=mean_lev,
        latency_seconds=result.latency_seconds,
    )


def run_evaluation(
    backend_url: str,
    dataset_root: Path,
    models: list[str],
    repetitions: int,
    limit: int | None = None,
) -> list[ModelReport]:
    """Execute the full evaluation loop.

    For each model, iterates over every document type folder and every
    document, sends the file to the backend, evaluates the response,
    and aggregates metrics into a :class:`ModelReport`.

    Args:
        backend_url: Backend base URL.
        dataset_root: Root of the dataset directory.
        models: List of ``llm_model`` identifiers to evaluate.
        repetitions: Number of times to repeat each extraction.

    Returns:
        One :class:`ModelReport` per model.
    """
    dataset = dataset_loader.discover_dataset(dataset_root)
    if not dataset:
        print(f"[WARN] No dataset folders found in {dataset_root}")
        return []

    reports: list[ModelReport] = []

    with httpx.Client() as client:
        for model in models:
            print(f"\n{'='*60}")
            print(f"  Model: {model}")
            print(f"{'='*60}")

            evaluations: list[DocumentEvaluation] = []

            for folder_name, entries in dataset.items():
                if limit is not None:
                    entries = entries[:limit]
                print(f"\n  [{folder_name}] {len(entries)} document(s)")

                for entry in entries:
                    for rep in range(1, repetitions + 1):
                        result = extract_single(
                            client=client,
                            backend_url=backend_url,
                            dataset_root=dataset_root,
                            folder_name=folder_name,
                            entry=entry,
                            llm_model=model,
                            repetition=rep,
                        )

                        evaluation = evaluate_single(result, entry)
                        evaluations.append(evaluation)

                        if not result.success:
                            rep_label = f" (rep {rep}/{repetitions})" if repetitions > 1 else ""
                            print(f"    FAIL {entry.doc}{rep_label} ({result.error[:80]})")
                        else:
                            mismatches = [c for c in evaluation.field_comparisons if not c.match]
                            if mismatches:
                                rep_label = f" (rep {rep}/{repetitions})" if repetitions > 1 else ""
                                print(f"    ERRO {entry.doc}{rep_label}  (F1={evaluation.f1:.2f})")
                                for m in mismatches:
                                    print(f"         {m.field_name}: esperado='{m.expected}' | extraido='{m.predicted}'")

            total = len(evaluations)
            if total == 0:
                reports.append(
                    ModelReport(
                        model=model,
                        total_documents=0,
                        mean_latency=0.0,
                        mean_f1=0.0,
                        mean_precision=0.0,
                        mean_recall=0.0,
                        mean_accuracy=0.0,
                        mean_levenshtein=0.0,
                        document_evaluations=[],
                    )
                )
                continue

            mean_latency = sum(e.latency_seconds for e in evaluations) / total
            mean_f1 = sum(e.f1 for e in evaluations) / total
            mean_precision = sum(e.precision for e in evaluations) / total
            mean_recall = sum(e.recall for e in evaluations) / total
            mean_accuracy = sum(e.accuracy for e in evaluations) / total
            mean_levenshtein = sum(e.mean_levenshtein for e in evaluations) / total

            reports.append(
                ModelReport(
                    model=model,
                    total_documents=total,
                    mean_latency=mean_latency,
                    mean_f1=mean_f1,
                    mean_precision=mean_precision,
                    mean_recall=mean_recall,
                    mean_accuracy=mean_accuracy,
                    mean_levenshtein=mean_levenshtein,
                    document_evaluations=evaluations,
                )
            )

    return reports
