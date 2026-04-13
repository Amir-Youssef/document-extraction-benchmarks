#!/usr/bin/env python3
"""Runner — CLI entry-point for the experiment module.

Usage examples::

    # Run all models over the full dataset
    python -m experiments.runner \\
        --dataset ./data/experiment_dataset \\
        --models gemini-pro gemini-flash \\
        --url http://localhost:8000

    # 3 repetitions, custom output path
    python -m experiments.runner \\
        --dataset ./data/experiment_dataset \\
        --models gemini-pro \\
        --url http://localhost:8000 \\
        --repetitions 3 \\
        --output ./results/report.json

    # Run only a subset of document-type folders
    python -m experiments.runner \\
        --dataset ./data/experiment_dataset \\
        --models gemini-flash \\
        --url http://localhost:8000 \\
        --folders cnh certificate
"""

import argparse
import sys
from pathlib import Path

from experiments.config import (
    fetch_available_models,
    resolve_backend_type,
    validate_type_mapping,
)
from experiments.dataset_loader import discover_dataset
from experiments.evaluator import run_evaluation
from experiments.report import export_json, print_summary


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="experiments.runner",
        description="Run model evaluation experiments against the Doc Extractor backend.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to the root dataset directory.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help=(
            "One or more llm_model identifiers (e.g. gemini-pro gemini-flash). "
            "If omitted, all models available in the backend are used."
        ),
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the backend (default: http://localhost:8000).",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Number of repetitions per document (default: 1).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/experiment_report.json"),
        help="Output path for the JSON report (default: experiment_report.json).",
    )
    parser.add_argument(
        "--folders",
        nargs="*",
        default=None,
        help="Optional subset of dataset folders to evaluate (by folder name).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of documents per folder (default: all).",
    )
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    """Validate parsed CLI arguments.

    Exits with code 1 on validation failure.

    Args:
        args: Parsed arguments namespace.
    """
    if not args.dataset.exists():
        print(f"[ERROR] Dataset path does not exist: {args.dataset}", file=sys.stderr)
        sys.exit(1)
    if not args.dataset.is_dir():
        print(f"[ERROR] Dataset path is not a directory: {args.dataset}", file=sys.stderr)
        sys.exit(1)
    if args.repetitions < 1:
        print("[ERROR] Repetitions must be >= 1.", file=sys.stderr)
        sys.exit(1)


def _filter_dataset(dataset_root: Path, folder_filter: list[str] | None) -> Path:
    """Optionally validate that requested folders exist in the dataset.

    This does not create a new directory — it simply validates the
    filter list against the discovered folders and prints a warning for
    any missing ones.

    Args:
        dataset_root: Root dataset directory.
        folder_filter: Optional list of folder names to include.

    Returns:
        The original *dataset_root* (unchanged).
    """
    if folder_filter is None:
        return dataset_root

    available = discover_dataset(dataset_root)
    for name in folder_filter:
        if name not in available:
            print(f"[WARN] Folder '{name}' not found in dataset, skipping.", file=sys.stderr)
    return dataset_root


def main() -> None:
    """Entry-point: parse args, run evaluation, print + export report."""
    parser = _build_parser()
    args = parser.parse_args()
    _validate_args(args)

    dataset_root: Path = args.dataset.resolve()
    backend_url: str = args.url
    repetitions: int = args.repetitions
    output_path: Path = args.output
    folder_filter: list[str] | None = args.folders

    # ── Modelos: buscar do backend ou usar os informados via CLI ──
    if args.models is None:
        print(f"[INFO] --models não informado. Consultando backend em {backend_url} ...")
        models: list[str] = fetch_available_models(backend_url)
        print(f"[INFO] Modelos encontrados: {', '.join(models)}")
    else:
        models = args.models

    _filter_dataset(dataset_root, folder_filter)

    # ── Folder filter via monkeypatch ──
    if folder_filter is not None:
        from experiments import dataset_loader

        _original_discover = dataset_loader.discover_dataset

        def _filtered_discover(root: Path) -> dict[str, list[object]]:  # type: ignore[override]
            full = _original_discover(root)
            return {k: v for k, v in full.items() if k in folder_filter}  # type: ignore[return-value]

        dataset_loader.discover_dataset = _filtered_discover  # type: ignore[assignment]

    # ── Validar mapeamento de tipos do dataset → backend ──
    dataset = discover_dataset(dataset_root)
    dataset_types: set[str] = set()
    for entries in dataset.values():
        for entry in entries:
            dataset_types.add(entry.tipo)
    validate_type_mapping(backend_url, dataset_types)

    # ── Mostrar mapeamento de tipos para o usuário ──
    print("\nMapeamento de tipos (dataset → backend):")
    for dt in sorted(dataset_types):
        print(f"  {dt} → {resolve_backend_type(dt)}")

    print(f"\nDataset:     {dataset_root}")
    print(f"Models:      {', '.join(models)}")
    print(f"Backend:     {backend_url}")
    print(f"Repetitions: {repetitions}")
    if folder_filter:
        print(f"Folders:     {', '.join(folder_filter)}")
    if args.limit:
        print(f"Limit:       {args.limit} doc(s) per folder")

    reports = run_evaluation(
        backend_url=backend_url,
        dataset_root=dataset_root,
        models=models,
        repetitions=repetitions,
        limit=args.limit,
    )

    print_summary(reports)
    export_json(reports, output_path)


if __name__ == "__main__":
    main()
