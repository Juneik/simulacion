"""Tarjeta de puntuación y reglas de anotación del Yahtzee clásico.

FASE USA. Trece categorías, bonus de la sección superior (35 puntos si la
suma es al menos 63) y la versión simplificada del Yahtzee adicional
descrita en la especificación del proyecto:

- Si sale un Yahtzee y la casilla Yahtzee ya vale 50, se suman +100.
- Esa tirada debe anotarse en otra casilla: primero la casilla superior del
  número obtenido, si sigue abierta; si no, cualquier casilla inferior abierta,
  puntuada como comodín (full = 25, escalera pequeña = 30, escalera grande = 40).
- Si la casilla Yahtzee está en 0 no hay bonus de +100, pero el comodín
  sigue aplicando.
- Si no queda casilla inferior, se anota 0 en una casilla superior abierta.
"""

from __future__ import annotations

from collections import Counter

UPPER_CATEGORIES: tuple[str, ...] = (
    "ones",
    "twos",
    "threes",
    "fours",
    "fives",
    "sixes",
)
LOWER_CATEGORIES: tuple[str, ...] = (
    "three_of_a_kind",
    "four_of_a_kind",
    "full_house",
    "small_straight",
    "large_straight",
    "yahtzee",
    "chance",
)
ALL_CATEGORIES: tuple[str, ...] = UPPER_CATEGORIES + LOWER_CATEGORIES

FACE_OF: dict[str, int] = {
    "ones": 1,
    "twos": 2,
    "threes": 3,
    "fours": 4,
    "fives": 5,
    "sixes": 6,
}
CATEGORY_OF_FACE: dict[int, str] = {face: name for name, face in FACE_OF.items()}

UPPER_BONUS_THRESHOLD = 63
UPPER_BONUS_POINTS = 35
YAHTZEE_SCORE = 50
YAHTZEE_BONUS_POINTS = 100

CATEGORY_LABELS: dict[str, str] = {
    "ones": "Unos",
    "twos": "Doses",
    "threes": "Treses",
    "fours": "Cuatros",
    "fives": "Cincos",
    "sixes": "Seises",
    "three_of_a_kind": "Trío",
    "four_of_a_kind": "Póker",
    "full_house": "Full",
    "small_straight": "Escalera pequeña",
    "large_straight": "Escalera grande",
    "yahtzee": "Yahtzee",
    "chance": "Chance",
}


def is_yahtzee(dice: list[int]) -> bool:
    """Cinco dados iguales."""
    return len(dice) == 5 and all(face == dice[0] for face in dice)


def raw_score(category: str, dice: list[int]) -> int:
    """Puntos de una categoría sin aplicar la regla de comodín."""
    if category not in ALL_CATEGORIES:
        raise KeyError(f"Categoría desconocida: {category}")
    counts = Counter(dice)
    if category in FACE_OF:
        face = FACE_OF[category]
        return counts[face] * face
    if category == "three_of_a_kind":
        return sum(dice) if any(count >= 3 for count in counts.values()) else 0
    if category == "four_of_a_kind":
        return sum(dice) if any(count >= 4 for count in counts.values()) else 0
    if category == "full_house":
        return 25 if sorted(counts.values()) == [2, 3] else 0
    if category == "small_straight":
        unique = set(dice)
        sequences = ({1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6})
        return 30 if any(sequence.issubset(unique) for sequence in sequences) else 0
    if category == "large_straight":
        unique = set(dice)
        return 40 if unique in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0
    if category == "yahtzee":
        return YAHTZEE_SCORE if is_yahtzee(dice) else 0
    return sum(dice)


def joker_score(category: str, dice: list[int]) -> int:
    """Puntos cuando un Yahtzee adicional se anota fuera de su casilla.

    La sección inferior se considera cumplida. Otra casilla superior distinta
    del número obtenido vale 0.
    """
    if not is_yahtzee(dice):
        raise ValueError("La puntuación de comodín exige cinco dados iguales.")
    if category in FACE_OF:
        return 5 * FACE_OF[category] if FACE_OF[category] == dice[0] else 0
    if category == "full_house":
        return 25
    if category == "small_straight":
        return 30
    if category == "large_straight":
        return 40
    if category in ("three_of_a_kind", "four_of_a_kind", "chance"):
        return sum(dice)
    if category == "yahtzee":
        return YAHTZEE_SCORE
    raise KeyError(f"Categoría desconocida: {category}")


class Scorecard:
    """Trece casillas, bonus superior y bonuses de Yahtzee adicional."""

    def __init__(self) -> None:
        self.scores: dict[str, int | None] = {category: None for category in ALL_CATEGORIES}
        self.yahtzee_bonuses = 0

    def is_open(self, category: str) -> bool:
        return self.scores[category] is None

    def open_categories(self) -> list[str]:
        return [category for category in ALL_CATEGORIES if self.scores[category] is None]

    def is_complete(self) -> bool:
        return all(score is not None for score in self.scores.values())

    def joker_rules_apply(self, dice: list[int]) -> bool:
        """El comodín rige si sale Yahtzee y esa casilla ya fue utilizada."""
        return is_yahtzee(dice) and self.scores["yahtzee"] is not None

    def yahtzee_bonus_available(self, dice: list[int]) -> bool:
        """+100 solo si la casilla Yahtzee se anotó con 50, no con 0."""
        return is_yahtzee(dice) and self.scores["yahtzee"] == YAHTZEE_SCORE

    def legal_categories(self, dice: list[int]) -> list[str]:
        """Casillas en las que esta tirada puede anotarse."""
        if not self.joker_rules_apply(dice):
            return self.open_categories()
        matching_upper = CATEGORY_OF_FACE[dice[0]]
        if self.is_open(matching_upper):
            return [matching_upper]
        lower_open = [category for category in LOWER_CATEGORIES if self.is_open(category)]
        if lower_open:
            return lower_open
        return [category for category in UPPER_CATEGORIES if self.is_open(category)]

    def points_for(self, category: str, dice: list[int]) -> int:
        """Puntos que otorgaría ``category`` sin modificar la tarjeta."""
        if self.joker_rules_apply(dice):
            return joker_score(category, dice)
        return raw_score(category, dice)

    def assign(self, category: str, dice: list[int]) -> int:
        """Anota la tirada en una casilla legal y aplica el bonus si corresponde."""
        legal = self.legal_categories(dice)
        if category not in legal:
            raise ValueError(
                f"No se puede anotar '{category}' con {list(dice)}. Opciones: {legal}"
            )
        grant_bonus = self.yahtzee_bonus_available(dice)
        points = self.points_for(category, dice)
        self.scores[category] = points
        if grant_bonus:
            self.yahtzee_bonuses += 1
        return points

    def upper_subtotal(self) -> int:
        return sum(
            score for category, score in self.scores.items()
            if category in FACE_OF and score is not None
        )

    def upper_bonus(self) -> int:
        if self.upper_subtotal() >= UPPER_BONUS_THRESHOLD:
            return UPPER_BONUS_POINTS
        return 0

    def lower_subtotal(self) -> int:
        return sum(
            score for category, score in self.scores.items()
            if category in LOWER_CATEGORIES and score is not None
        )

    def yahtzee_bonus_points(self) -> int:
        return self.yahtzee_bonuses * YAHTZEE_BONUS_POINTS

    def total(self) -> int:
        return (
            self.upper_subtotal()
            + self.upper_bonus()
            + self.lower_subtotal()
            + self.yahtzee_bonus_points()
        )

    def breakdown(self) -> dict[str, int | dict[str, int | None]]:
        return {
            "categories": dict(self.scores),
            "upper_subtotal": self.upper_subtotal(),
            "upper_bonus": self.upper_bonus(),
            "lower_subtotal": self.lower_subtotal(),
            "yahtzee_bonuses": self.yahtzee_bonuses,
            "yahtzee_bonus_points": self.yahtzee_bonus_points(),
            "total": self.total(),
        }
