"""Small deterministic metric helpers for CI-friendly evaluation."""

from __future__ import annotations

from collections import Counter


def accuracy(expected: list[str], predicted: list[str]) -> float:
    if not expected:
        return 0.0
    correct = sum(1 for left, right in zip(expected, predicted, strict=True) if left == right)
    return round(correct / len(expected), 4)


def macro_f1(expected: list[str], predicted: list[str]) -> float:
    if not expected:
        return 0.0

    labels = sorted(set(expected) | set(predicted))
    scores: list[float] = []
    for label in labels:
        true_positive = sum(
            1
            for gold, pred in zip(expected, predicted, strict=True)
            if gold == label and pred == label
        )
        predicted_positive = Counter(predicted)[label]
        actual_positive = Counter(expected)[label]
        precision = true_positive / predicted_positive if predicted_positive else 0.0
        recall = true_positive / actual_positive if actual_positive else 0.0
        if precision + recall == 0:
            scores.append(0.0)
        else:
            scores.append(2 * precision * recall / (precision + recall))
    return round(sum(scores) / len(scores), 4)


def evidence_coverage(referenced_ids: set[str], known_ids: set[str]) -> float:
    if not referenced_ids:
        return 0.0
    covered = len(referenced_ids & known_ids)
    return round(covered / len(referenced_ids), 4)
