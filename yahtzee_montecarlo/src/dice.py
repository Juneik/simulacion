"""Dados del Yahtzee clásico.

FASE USA. Un turno comienza con cinco dados de seis caras. Después del
primer y del segundo lanzamiento el jugador puede conservar cualquier
subconjunto y volver a lanzar el resto, hasta un máximo de tres lanzamientos.
"""

from __future__ import annotations

from numpy.random import Generator


class DiceSet:
    """Conjunto de dados y operaciones de lanzamiento y conservación."""

    def __init__(self, rng: Generator, count: int = 5, faces: int = 6) -> None:
        if count < 1:
            raise ValueError("Se requiere al menos un dado.")
        if faces < 2:
            raise ValueError("Un dado debe tener al menos dos caras.")
        self.rng = rng
        self.count = count
        self.faces = faces
        self.values: list[int] = [1] * count

    def roll_all(self) -> list[int]:
        """Lanza todos los dados y devuelve una copia de los valores."""
        rolled = self.rng.integers(1, self.faces + 1, size=self.count)
        self.values = [int(v) for v in rolled]
        return list(self.values)

    def reroll(self, hold: set[int] | list[int]) -> list[int]:
        """Relanza los dados cuyo índice no está en ``hold``.

        Los índices son posiciones ``0 .. count-1``. Conservar todos los
        índices deja el resultado igual y no consume números aleatorios.
        """
        held = set(hold)
        unknown = held.difference(range(self.count))
        if unknown:
            raise IndexError(f"Índice de dado fuera de rango: {sorted(unknown)}")
        for index in range(self.count):
            if index not in held:
                self.values[index] = int(self.rng.integers(1, self.faces + 1))
        return list(self.values)
