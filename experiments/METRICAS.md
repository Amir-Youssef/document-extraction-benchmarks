# Evaluation Metrics — `experiments/metrics.py`

This document describes the metrics used by the experiments module to evaluate the quality of document data extraction.

All metrics operate on `field → value` dictionaries and are dynamically calculated over the **union of keys** from ground-truth and prediction — no field names are hard-coded.

---

## Text Normalization

Before any comparison, values pass through the `normalise()` function:

1. Converts to **lowercase**
2. Removes **spaces** at extremities (`strip`)
3. Collapses **multiple internal spaces** into a single space
4. Removes **accents/diacritics** (e.g., `ç` → `c`, `ã` → `a`)

This ensures that superficial formatting differences don't impact evaluation.

---

## Available Metrics

### 1. Accuracy

**Function:** `accuracy(expected, predicted) → float`

Proportion of fields whose normalized values match exactly.

$$\text{accuracy} = \frac{\text{correct fields}}{\text{total fields}}$$

- **Total fields** = union of keys from `expected` and `predicted`.
- A field absent in one of the dicts is treated as empty string (`""`).
- Returns `0.0` if both dicts are empty.

**Example:** if 7 out of 10 fields are correct → `accuracy = 0.7`.

---

### 2. Precision, Recall, and F1-Score

**Function:** `precision_recall_f1(expected, predicted) → (precision, recall, f1)`

Classic information retrieval metrics, applied at field level:

| Concept | Definition |
|---|---|
| **True Positive (TP)** | Field present in both dicts **and** values match |
| **False Positive (FP)** | Field present in `predicted` but absent in `expected`, **or** present in both but with different values |
| **False Negative (FN)** | Field present in `expected` but absent in `predicted`, **or** present in both but with different values |

> **Note:** when a field exists in both dicts but values diverge, it counts as both FP and FN.

**Formulas:**

$$\text{precision} = \frac{TP}{TP + FP}$$

$$\text{recall} = \frac{TP}{TP + FN}$$

$$F_1 = \frac{2 \times \text{precision} \times \text{recall}}{\text{precision} + \text{recall}}$$

- **Precision** answers: "of the fields the model returned, how many are correct?"
- **Recall** answers: "of the expected fields, how many did the model get right?"
- **F1** is the harmonic mean between precision and recall — balances both perspectives.

All return `0.0` when denominator is zero.

---

### 3. Levenshtein Similarity (Mean)

**Function:** `mean_levenshtein_similarity(expected, predicted) → float`

Measures how close extracted values are to expected ones, even when not identical.

**Calculation per field:**

$$\text{similarity} = 1 - \frac{\text{Levenshtein distance}(a, b)}{\max(|a|, |b|)}$$

- The **Levenshtein distance** counts the minimum number of character insertions, removals, or substitutions to transform one string into another.
- The resulting similarity is in the range `[0, 1]`: **1.0** = identical strings, **0.0** = completely different.
- Returns `1.0` when both strings are empty.

The final metric is the **mean** of similarity across all fields (union of keys).

**Usefulness:** captures partial matches. If the model extracted `"Joao da Silva"` and the expected is `"João da Silva"`, the similarity will be high even if exact comparison fails (before accent normalization).

---

### 4. Latency Statistics

**Function:** `compute_latency_stats(latencies) → dict`

Descriptive statistics about extraction execution times:

| Key | Description |
|---|---|
| `mean` | Average time (seconds) |
| `min` | Shortest recorded time |
| `max` | Longest recorded time |

Values rounded to 4 decimal places. Returns `0.0` for all if list is empty.

---

## Helper Functions

| Function | Description |
|---|---|
| `normalise(value)` | Normalizes a value for comparison (lower, strip, collapse spaces, remove accents) |
| `compute_field_matches(expected, predicted)` | Returns list of tuples `(field, expected_value, predicted_value, match)` for detailed field-by-field inspection |
| `_levenshtein_distance(a, b)` | Calculates edit distance between two strings (internal use) |
| `_strip_accents(value)` | Removes diacritics from a string (internal use) |

---

## Visual Summary

```
                    Exact Comparison          Partial Comparison
                   ┌─────────────────┐       ┌──────────────────┐
                   │  Accuracy        │       │  Levenshtein     │
                   │  Precision       │       │  Similarity      │
                   │  Recall          │       │                  │
                   │  F1-Score        │       │                  │
                   └─────────────────┘       └──────────────────┘

                    Performance
                   ┌─────────────────┐
                   │  Latency         │
                   │  (mean/min/max)  │
                   └─────────────────┘
```
