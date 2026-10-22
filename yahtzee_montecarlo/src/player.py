"""Jugadores y estrategias de decisión.

La política que viene de la guía del profesor está en ``guide_montecarlo``:
estima por Montecarlo cuál máscara de dados conviene conservar.

``RandomStrategy`` es la línea base de comparación: no interpreta la tirada.
``GreedyStrategy`` y ``UpperFocusStrategy`` son aportes propios. La primera
anota la categoría de mayor puntaje inmediato; la segunda persigue el bonus
de 35 puntos de la sección superior. Ninguna calcula el valor esperado óptimo
del juego completo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter

from numpy.random import Generator

from src.scorecard import (
    CATEGORY_LABELS,
    FACE_OF,
    LOWER_CATEGORIES,
    UPPER_CATEGORIES,
    Scorecard,
    is_yahtzee,
)

# Se anula primero la casilla con menor índice: es la menos útil cuando
# ninguna opción legal da puntos.
SACRIFICE_ORDER: tuple[str, ...] = (
    "ones",
    "twos",
    "yahtzee",
    "threes",
    "fours",
    "three_of_a_kind",
    "chance",
    "four_of_a_kind",
    "fives",
    "small_straight",
    "full_house",
    "sixes",
    "large_straight",
)

# La estrategia de sección superior protege las casillas altas.
UPPER_SACRIFICE_ORDER: tuple[str, ...] = (
    "yahtzee",
    "four_of_a_kind",
    "three_of_a_kind",
    "chance",
    "ones",
    "twos",
    "full_house",
    "small_straight",
    "threes",
    "large_straight",
    "fours",
    "fives",
    "sixes",
)

# Ante empate de puntos, se prefiere la combinación más difícil de repetir.
TIE_BREAK: dict[str, int] = {
    "yahtzee": 100,
    "large_straight": 90,
    "full_house": 80,
    "small_straight": 70,
    "sixes": 60,
    "fives": 55,
    "four_of_a_kind": 50,
    "fours": 40,
    "three_of_a_kind": 30,
    "threes": 25,
    "chance": 10,
    "twos": 5,
    "ones": 0,
}


class Strategy(ABC):
    """Política de conservación de dados y de elección de casilla."""

    name: str
    label: str

    @abstractmethod
    def choose_hold(
        self,
        dice: list[int],
        roll_number: int,
        card: Scorecard,
        rng: Generator,
    ) -> set[int] | None:
        """Índices que se conservan tras el lanzamiento ``roll_number`` (1 o 2).

        ``None`` termina el turno y pasa a anotar. Un conjunto vacío relanza
        los cinco dados.
        """

    @abstractmethod
    def choose_category(self, dice: list[int], card: Scorecard, rng: Generator) -> str:
        """Casilla legal en la que se anota la tirada final."""


def longest_run_holds(dice: list[int]) -> set[int]:
    """Conserva una copia de la secuencia consecutiva más larga."""
    first_index: dict[int, int] = {}
    for index, face in enumerate(dice):
        first_index.setdefault(face, index)
    best: list[int] = []
    for start in range(1, 7):
        run: list[int] = []
        face = start
        while face <= 6 and face in first_index:
            run.append(face)
            face += 1
        if len(run) > len(best):
            best = run
    return {first_index[face] for face in best}


def _best_positive(options: list[str], card: Scorecard, dice: list[int]) -> str | None:
    scored = [(card.points_for(category, dice), category) for category in options]
    best = max(points for points, _ in scored)
    if best <= 0:
        return None
    candidates = [category for points, category in scored if points == best]
    return max(candidates, key=lambda category: TIE_BREAK.get(category, 0))


def _sacrifice(options: list[str], order: tuple[str, ...]) -> str:
    return min(options, key=lambda category: order.index(category))


class RandomStrategy(Strategy):
    """FASE USA. No interpreta los dados: conserva y anota al azar."""

    name = "aleatoria"
    label = "Aleatoria"

    def choose_hold(self, dice, roll_number, card, rng):
        hold = {index for index in range(len(dice)) if float(rng.random()) < 0.5}
        if len(hold) == len(dice):
            hold.remove(int(rng.integers(0, len(dice))))
        return hold

    def choose_category(self, dice, card, rng):
        options = card.legal_categories(dice)
        return options[int(rng.integers(0, len(options)))]


class GreedyStrategy(Strategy):
    """FASE MODIFICA. Maximiza el puntaje visible en este turno."""

    name = "avida"
    label = "Ávida"
    sacrifice_order = SACRIFICE_ORDER

    def choose_hold(self, dice, roll_number, card, rng):
        if self._should_stand(dice, roll_number, card):
            return None
        return self._holds(dice, card)

    def _should_stand(self, dice: list[int], roll_number: int, card: Scorecard) -> bool:
        # Cinco iguales no mejoran al relanzar. La escalera grande tampoco.
        if is_yahtzee(dice):
            return True
        legal = card.legal_categories(dice)
        if "large_straight" in legal and card.points_for("large_straight", dice) == 40:
            return True
        if roll_number >= 2:
            best = max(card.points_for(category, dice) for category in legal)
            if best >= 25:
                return True
        return False

    def _holds(self, dice: list[int], card: Scorecard) -> set[int]:
        counts = Counter(dice)
        face, count = max(counts.items(), key=lambda item: (item[1], item[0]))
        if count >= 3:
            return {index for index, value in enumerate(dice) if value == face}

        straight_open = card.is_open("large_straight") or card.is_open("small_straight")
        straight = longest_run_holds(dice)
        if straight_open and len(straight) >= 4:
            return straight
        if straight_open and len(straight) >= 3 and count < 2:
            return straight

        pairs = [value for value, times in counts.items() if times >= 2]
        if len(pairs) >= 2 and card.is_open("full_house"):
            return {index for index, value in enumerate(dice) if counts[value] >= 2}
        if count >= 2:
            return {index for index, value in enumerate(dice) if value == face}
        if straight:
            return straight
        return set()

    def choose_category(self, dice, card, rng):
        options = card.legal_categories(dice)
        if len(options) == 1:
            return options[0]
        chosen = _best_positive(options, card, dice)
        if chosen is not None:
            return chosen
        return _sacrifice(options, self.sacrifice_order)


class UpperFocusStrategy(GreedyStrategy):
    """FASE MODIFICA. Prioriza tres o más dados de cada número superior.

    El bonus de 35 exige al menos 63 en la sección superior, es decir, un
    promedio de tres dados por número. Mientras esa sección esté abierta,
    la política persigue ese umbral y solo desvía la tirada hacia una
    casilla inferior cuando el puntaje inmediato es claramente alto.
    """

    name = "seccion_superior"
    label = "Sección superior"
    sacrifice_order = UPPER_SACRIFICE_ORDER

    def choose_hold(self, dice, roll_number, card, rng):
        if is_yahtzee(dice):
            return None
        if card.is_open("large_straight") and card.points_for("large_straight", dice) == 40:
            return None
        target = self._target_face(dice, card)
        if target is not None:
            return {index for index, value in enumerate(dice) if value == target}
        return super().choose_hold(dice, roll_number, card, rng)

    def _target_face(self, dice: list[int], card: Scorecard) -> int | None:
        open_faces = [FACE_OF[category] for category in UPPER_CATEGORIES if card.is_open(category)]
        if not open_faces:
            return None
        best = max(open_faces, key=lambda face: (dice.count(face), face))
        # Sin al menos una pareja no hay tracción: se usa la heurística general.
        if dice.count(best) >= 2:
            return best
        return None

    def choose_category(self, dice, card, rng):
        options = card.legal_categories(dice)
        if len(options) == 1:
            return options[0]

        def points(category: str) -> int:
            return card.points_for(category, dice)

        upper_options = [category for category in options if category in FACE_OF]
        qualified = [
            category
            for category in upper_options
            if points(category) >= 3 * FACE_OF[category]
        ]
        if qualified:
            return max(
                qualified,
                key=lambda category: (points(category) - 3 * FACE_OF[category], FACE_OF[category]),
            )

        lower_options = [category for category in options if category in LOWER_CATEGORIES]
        if lower_options:
            best_lower = max(lower_options, key=lambda category: (points(category), TIE_BREAK.get(category, 0)))
            if points(best_lower) >= 25:
                return best_lower
        else:
            best_lower = None

        short_upper = [category for category in upper_options if points(category) > 0]
        boxes_left = len(card.open_categories())
        late = boxes_left <= 4 or card.upper_subtotal() >= 48
        if short_upper and late:
            return max(short_upper, key=lambda category: (points(category), FACE_OF[category]))

        decent_upper = [
            category
            for category in short_upper
            if FACE_OF[category] >= 4 and points(category) >= 2 * FACE_OF[category]
        ]
        if decent_upper and card.upper_subtotal() < 63:
            return max(decent_upper, key=lambda category: (points(category), FACE_OF[category]))

        if best_lower is not None and points(best_lower) > 0:
            return best_lower
        if short_upper and (best_lower is None or points(best_lower) == 0):
            return max(short_upper, key=lambda category: (points(category), FACE_OF[category]))
        return super().choose_category(dice, card, rng)


from src.guide_montecarlo import MonteCarloStrategy

STRATEGIES: dict[str, type[Strategy]] = {
    "aleatoria": RandomStrategy,
    "avida": GreedyStrategy,
    "seccion_superior": UpperFocusStrategy,
    "montecarlo": MonteCarloStrategy,
}

STRATEGY_ALIASES: dict[str, str] = {
    "random": "aleatoria",
    "greedy": "avida",
    "upper": "seccion_superior",
    "upper_focus": "seccion_superior",
    "guia": "montecarlo",
    "mc": "montecarlo",
}


def make_strategy(name: str, sims_per_mask: int = 24) -> Strategy:
    """Construye la política. ``sims_per_mask`` solo afecta a Montecarlo."""
    kind = resolve_strategy(name)
    if kind is MonteCarloStrategy:
        return MonteCarloStrategy(sims_per_mask)
    return kind()


def resolve_strategy(name: str) -> type[Strategy]:
    key = STRATEGY_ALIASES.get(name.strip().lower(), name.strip().lower())
    try:
        return STRATEGIES[key]
    except KeyError as error:
        known = ", ".join(STRATEGIES)
        raise KeyError(f"Estrategia desconocida: '{name}'. Opciones: {known}") from error


class Player:
    """Participante con tarjeta propia y una estrategia de decisión."""

    def __init__(self, name: str, strategy: Strategy) -> None:
        self.name = name
        self.strategy = strategy
        self.scorecard = Scorecard()
        self.yahtzees_rolled = 0

    def summary(self) -> dict[str, object]:
        card = self.scorecard.breakdown()
        return {
            "name": self.name,
            "strategy": self.strategy.name,
            "strategy_label": self.strategy.label,
            "yahtzees_rolled": self.yahtzees_rolled,
            **card,
        }


def format_dice(dice: list[int]) -> str:
    return "[" + ", ".join(str(value) for value in dice) + "]"


def format_category(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)
