"""Metrics — field-level comparison and aggregate scoring.

All metrics are computed dynamically over whatever keys appear in the
ground-truth ``respostas`` dict.  No field names are hard-coded.
"""

import re
import unicodedata


def _strip_accents(value: str) -> str:
    """Remove diacritical marks (accents) from text."""
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


_PUNCTUATION = set(".,;:-")


def normalise(value: object) -> str:
    """Lower-case, strip accents, remove punctuation (. , : ; -) and collapse whitespace.

    Args:
        value: Raw value (coerced to str if not already).

    Returns:
        Normalised string for comparison.
    """
    text = value if isinstance(value, str) else str(value)
    text = "".join(c for c in text if c not in _PUNCTUATION)
    text = _strip_accents(text.lower().strip())
    return re.sub(r"\s{2,}", " ", text)


def compute_field_matches(
    expected: dict[str, str],
    predicted: dict[str, str],
) -> list[tuple[str, str, str, bool]]:
    """Compare two field dicts after normalisation.

    For every key in the **union** of *expected* and *predicted*:

    * If a key exists only in *expected* → miss (match=False).
    * If a key exists only in *predicted* → spurious (match=False).
    * If both exist → compare normalised values.

    Args:
        expected: Ground-truth field→value mapping.
        predicted: Model-returned field→value mapping.

    Returns:
        List of ``(field_name, normalised_expected, normalised_predicted, match)``
        tuples covering all keys from the union of both dicts.
    """
    all_keys = sorted(set(expected.keys()) | set(predicted.keys()))
    results: list[tuple[str, str, str, bool]] = []
    for key in all_keys:
        exp = normalise(expected.get(key, ""))
        pred = normalise(predicted.get(key, ""))
        results.append((key, exp, pred, exp == pred))
    return results


def precision_recall_f1(
    expected: dict[str, str],
    predicted: dict[str, str],
) -> tuple[float, float, float]:
    """Compute precision, recall and F1 at field level.

    * **True Positive (TP):** key present in both *and* values match.
    * **False Positive (FP):** key in *predicted* but not in *expected*,
      or key in both but values differ.
    * **False Negative (FN):** key in *expected* but not in *predicted*,
      or key in both but values differ.

    Args:
        expected: Ground-truth mapping.
        predicted: Model-returned mapping.

    Returns:
        ``(precision, recall, f1)`` as floats in [0, 1].
    """
    tp = 0
    fp = 0
    fn = 0

    all_keys = set(expected.keys()) | set(predicted.keys())
    for key in all_keys:
        exp_val = normalise(expected.get(key, ""))
        pred_val = normalise(predicted.get(key, ""))

        in_expected = key in expected
        in_predicted = key in predicted

        if in_expected and in_predicted and exp_val == pred_val:
            tp += 1
        else:
            if in_predicted:
                fp += 1
            if in_expected:
                fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def _levenshtein_distance(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings.

    Uses the classic dynamic-programming matrix approach.
    """
    if len(a) < len(b):
        return _levenshtein_distance(b, a)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def levenshtein_similarity(a: str, b: str) -> float:
    """Return a similarity score in [0, 1] based on Levenshtein distance.

    Formula: ``1 - (distance / max(len(a), len(b)))``

    Returns 1.0 when both strings are empty.
    """
    if not a and not b:
        return 1.0
    max_len = max(len(a), len(b))
    return 1.0 - (_levenshtein_distance(a, b) / max_len)


def mean_levenshtein_similarity(
    expected: dict[str, str],
    predicted: dict[str, str],
) -> float:
    """Compute the mean Levenshtein similarity across all fields.

    Uses the union of keys from *expected* and *predicted*, normalising
    values before comparison (same logic as other metrics).

    Returns 0.0 when both dicts are empty.
    """
    all_keys = set(expected.keys()) | set(predicted.keys())
    if not all_keys:
        return 0.0
    total = sum(
        levenshtein_similarity(
            normalise(expected.get(key, "")),
            normalise(predicted.get(key, "")),
        )
        for key in all_keys
    )
    return total / len(all_keys)


def accuracy(expected: dict[str, str], predicted: dict[str, str]) -> float:
    """Compute accuracy over the union of field keys.

    ``accuracy = matching_fields / total_fields``

    Args:
        expected: Ground-truth mapping.
        predicted: Model-returned mapping.

    Returns:
        Accuracy as a float in [0, 1].  Returns 0.0 when both dicts
        are empty.
    """
    all_keys = set(expected.keys()) | set(predicted.keys())
    if not all_keys:
        return 0.0
    matches = sum(
        1
        for key in all_keys
        if normalise(expected.get(key, "")) == normalise(predicted.get(key, ""))
    )
    return matches / len(all_keys)


def compute_latency_stats(latencies: list[float]) -> dict[str, float]:
    """Compute average, min and max latency.

    Args:
        latencies: List of execution times in seconds.

    Returns:
        Dict with 'mean', 'min', and 'max' latency rounded to 4 decimals.
    """
    if not latencies:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(sum(latencies) / len(latencies), 4),
        "min": round(min(latencies), 4),
        "max": round(max(latencies), 4),
    }
