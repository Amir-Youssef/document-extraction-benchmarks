"""Report — builds and exports the final experiment report.

Supports:
* Pretty-printed console summary
* JSON export
"""

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from experiments.experiment_types import DocumentEvaluation, ModelReport


def print_summary(reports: list[ModelReport]) -> None:
    """Print a human-readable summary table to stdout.

    Args:
        reports: List of model reports to display.
    """
    if not reports:
        print("\n[REPORT] No results to display.")
        return

    header = (
        f"{'Model':<25} {'Docs':>5} {'Latency':>9} "
        f"{'F1':>7} {'Prec':>7} {'Recall':>7} {'Acc':>7} {'Lev':>7}"
    )
    separator = "-" * len(header)

    print(f"\n{'='*len(header)}")
    print("  EXPERIMENT REPORT")
    print(f"{'='*len(header)}")
    print(header)
    print(separator)

    for r in reports:
        print(
            f"{r.model:<25} {r.total_documents:>5} "
            f"{r.mean_latency:>8.2f}s "
            f"{r.mean_f1:>7.4f} {r.mean_precision:>7.4f} "
            f"{r.mean_recall:>7.4f} {r.mean_accuracy:>7.4f} "
            f"{r.mean_levenshtein:>7.4f}"
        )

    print(separator)


def _build_field_metrics_by_type(
    evaluations: list[DocumentEvaluation],
) -> dict[str, dict[str, dict[str, float]]]:
    """Compute per-field average metrics grouped by document type.

    Returns a dict like::

        {
            "arrais": {
                "nome": {"accuracy": 0.95, "mean_levenshtein": 0.97},
                "cpf":  {"accuracy": 0.90, "mean_levenshtein": 0.92},
            },
            ...
        }
    """
    # Accumulate: doc_type → field_name → list of (match, levenshtein)
    acc: dict[str, dict[str, list[tuple[bool, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for ev in evaluations:
        for fc in ev.field_comparisons:
            acc[ev.document_type][fc.field_name].append(
                (fc.match, fc.levenshtein_similarity)
            )

    result: dict[str, dict[str, dict[str, float]]] = {}
    for doc_type, fields in sorted(acc.items()):
        result[doc_type] = {}
        for field_name, values in sorted(fields.items()):
            total = len(values)
            result[doc_type][field_name] = {
                "accuracy": sum(1 for m, _ in values if m) / total,
                "mean_levenshtein": sum(lev for _, lev in values) / total,
            }

    return result


def export_json(reports: list[ModelReport], output_path: Path) -> None:
    """Export the full report to a JSON file.

    Includes aggregate metrics for each model, per-field averages grouped
    by document type, and only the document evaluations that had at least
    one field mismatch.

    Args:
        reports: List of model reports to serialise.
        output_path: Destination file path (will be created / overwritten).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = []
    for r in reports:
        failed_evals = [
            asdict(e)
            for e in r.document_evaluations
            if any(not c.match for c in e.field_comparisons)
        ]
        payload.append(
            {
                "model": r.model,
                "total_documents": r.total_documents,
                "mean_latency": r.mean_latency,
                "mean_f1": r.mean_f1,
                "mean_precision": r.mean_precision,
                "mean_recall": r.mean_recall,
                "mean_accuracy": r.mean_accuracy,
                "mean_levenshtein": r.mean_levenshtein,
                "field_metrics_by_type": _build_field_metrics_by_type(
                    r.document_evaluations
                ),
                "documents_with_errors": len(failed_evals),
                "document_evaluations": failed_evals,
            }
        )

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f"\n[REPORT] JSON exported to {output_path}")
