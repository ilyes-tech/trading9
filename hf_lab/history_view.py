"""Vues chronologiques bornées sans copie croissante de l'historique."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Generic, TypeVar, overload


Item = TypeVar("Item")


class VisibleHistory(
    Sequence[Item],
    Generic[Item],
):
    """Expose uniquement ``source[0:stop]`` sans copier ce préfixe.

    Un accès direct au futur est impossible. Les petites tranches
    demandées par les indicateurs sont matérialisées sous forme de tuple.
    """

    __slots__ = (
        "_source",
        "_stop",
    )

    def __init__(
        self,
        source: Sequence[Item],
        stop: int,
    ) -> None:
        source_length = len(source)

        if not 0 <= stop <= source_length:
            raise ValueError(
                "Limite VisibleHistory invalide : "
                f"stop={stop}, source={source_length}"
            )

        self._source = source
        self._stop = stop

    def __len__(self) -> int:
        return self._stop

    @overload
    def __getitem__(
        self,
        index: int,
    ) -> Item:
        ...

    @overload
    def __getitem__(
        self,
        index: slice,
    ) -> tuple[Item, ...]:
        ...

    def __getitem__(
        self,
        index: int | slice,
    ) -> Item | tuple[Item, ...]:
        if isinstance(index, slice):
            start, stop, step = index.indices(
                self._stop
            )

            return tuple(
                self._source[position]
                for position in range(
                    start,
                    stop,
                    step,
                )
            )

        normalized = index

        if normalized < 0:
            normalized += self._stop

        if (
            normalized < 0
            or normalized >= self._stop
        ):
            raise IndexError(
                "VisibleHistory index hors limite"
            )

        return self._source[
            normalized
        ]

    def __iter__(self) -> Iterator[Item]:
        for position in range(
            self._stop
        ):
            yield self._source[
                position
            ]
