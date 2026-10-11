"""Séparation chronologique entraînement, validation et test."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar


Item = TypeVar("Item")


@dataclass(frozen=True)
class ChronologicalSplit(
    Generic[Item]
):
    train: tuple[Item, ...]
    validation: tuple[Item, ...]
    test: tuple[Item, ...]


def chronological_split(
    items: Sequence[Item],
    *,
    train_ratio: float = 0.60,
    validation_ratio: float = 0.20,
    test_ratio: float = 0.20,
) -> ChronologicalSplit[Item]:
    total_ratio = (
        train_ratio
        + validation_ratio
        + test_ratio
    )

    if abs(
        total_ratio
        - 1.0
    ) > 1e-9:
        raise ValueError(
            "Les ratios doivent totaliser 1."
        )

    if len(items) < 15:
        raise ValueError(
            "Historique insuffisant pour une séparation fiable."
        )

    if min(
        train_ratio,
        validation_ratio,
        test_ratio,
    ) <= 0:
        raise ValueError(
            "Chaque partie doit être non vide."
        )

    train_end = int(
        len(items)
        * train_ratio
    )

    validation_end = (
        train_end
        + int(
            len(items)
            * validation_ratio
        )
    )

    train = tuple(
        items[:train_end]
    )

    validation = tuple(
        items[
            train_end:validation_end
        ]
    )

    test = tuple(
        items[validation_end:]
    )

    if not train or not validation or not test:
        raise ValueError(
            "Une partie de l'historique est vide."
        )

    return ChronologicalSplit(
        train=train,
        validation=validation,
        test=test,
    )
