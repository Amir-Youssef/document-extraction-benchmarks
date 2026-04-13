# Métricas de Avaliação — `experiments/metrics.py`

Este documento descreve as métricas utilizadas pelo módulo de experimentos para avaliar a qualidade da extração de dados dos documentos.

Todas as métricas operam sobre dicionários `campo → valor` e são calculadas dinamicamente sobre a **união das chaves** do ground-truth e da predição — nenhum nome de campo é hard-coded.

---

## Normalização de Texto

Antes de qualquer comparação, os valores passam pela função `normalise()`:

1. Converte para **minúsculas**
2. Remove **espaços** nas extremidades (`strip`)
3. Colapsa **espaços internos** múltiplos em um único espaço
4. Remove **acentos/diacríticos** (ex: `ç` → `c`, `ã` → `a`)

Isso garante que diferenças superficiais de formatação não impactem a avaliação.

---

## Métricas Disponíveis

### 1. Accuracy (Acurácia)

**Função:** `accuracy(expected, predicted) → float`

Proporção de campos cujos valores normalizados coincidem exatamente.

$$\text{accuracy} = \frac{\text{campos corretos}}{\text{total de campos}}$$

- **Total de campos** = união das chaves de `expected` e `predicted`.
- Um campo ausente em um dos dicts é tratado como string vazia (`""`).
- Retorna `0.0` se ambos os dicts forem vazios.

**Exemplo:** se 7 de 10 campos estão corretos → `accuracy = 0.7`.

---

### 2. Precision, Recall e F1-Score

**Função:** `precision_recall_f1(expected, predicted) → (precision, recall, f1)`

Métricas clássicas de recuperação de informação, aplicadas no nível de campos:

| Conceito | Definição |
|---|---|
| **True Positive (TP)** | Campo presente em ambos os dicts **e** valores coincidem |
| **False Positive (FP)** | Campo presente em `predicted` mas ausente em `expected`, **ou** presente em ambos mas com valores diferentes |
| **False Negative (FN)** | Campo presente em `expected` mas ausente em `predicted`, **ou** presente em ambos mas com valores diferentes |

> **Nota:** quando um campo existe em ambos os dicts mas os valores divergem, ele conta tanto como FP quanto como FN.

**Fórmulas:**

$$\text{precision} = \frac{TP}{TP + FP}$$

$$\text{recall} = \frac{TP}{TP + FN}$$

$$F_1 = \frac{2 \times \text{precision} \times \text{recall}}{\text{precision} + \text{recall}}$$

- **Precision** responde: "dos campos que o modelo retornou, quantos estão corretos?"
- **Recall** responde: "dos campos esperados, quantos o modelo acertou?"
- **F1** é a média harmônica entre precision e recall — equilibra ambas as perspectivas.

Todas retornam `0.0` quando o denominador é zero.

---

### 3. Similaridade de Levenshtein (Média)

**Função:** `mean_levenshtein_similarity(expected, predicted) → float`

Mede quão próximos os valores extraídos estão dos esperados, mesmo quando não são idênticos.

**Cálculo por campo:**

$$\text{similaridade} = 1 - \frac{\text{distância de Levenshtein}(a, b)}{\max(|a|, |b|)}$$

- A **distância de Levenshtein** conta o número mínimo de inserções, remoções ou substituições de caracteres para transformar uma string na outra.
- A similaridade resultante está no intervalo `[0, 1]`: **1.0** = strings idênticas, **0.0** = completamente diferentes.
- Retorna `1.0` quando ambas as strings são vazias.

A métrica final é a **média** da similaridade sobre todos os campos (união de chaves).

**Utilidade:** captura acertos parciais. Se o modelo extraiu `"Joao da Silva"` e o esperado é `"João da Silva"`, a similaridade será alta mesmo que a comparação exata falhe (antes da normalização de acentos).

---

### 4. Estatísticas de Latência

**Função:** `compute_latency_stats(latencies) → dict`

Estatísticas descritivas sobre os tempos de execução das extrações:

| Chave | Descrição |
|---|---|
| `mean` | Tempo médio (segundos) |
| `min` | Menor tempo registrado |
| `max` | Maior tempo registrado |

Valores arredondados a 4 casas decimais. Retorna `0.0` para todos se a lista estiver vazia.

---

## Funções Auxiliares

| Função | Descrição |
|---|---|
| `normalise(value)` | Normaliza um valor para comparação (lower, strip, collapse spaces, remove accents) |
| `compute_field_matches(expected, predicted)` | Retorna lista de tuplas `(campo, valor_esperado, valor_predito, match)` para inspeção detalhada campo a campo |
| `_levenshtein_distance(a, b)` | Calcula a distância de edição entre duas strings (uso interno) |
| `_strip_accents(value)` | Remove diacríticos de uma string (uso interno) |

---

## Resumo Visual

```
                    Comparação Exata          Comparação Parcial
                   ┌─────────────────┐       ┌──────────────────┐
                   │  Accuracy        │       │  Levenshtein     │
                   │  Precision       │       │  Similarity      │
                   │  Recall          │       │                  │
                   │  F1-Score        │       │                  │
                   └─────────────────┘       └──────────────────┘

                    Performance
                   ┌─────────────────┐
                   │  Latência        │
                   │  (mean/min/max)  │
                   └─────────────────┘
```
