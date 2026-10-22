"""Motor de Montecarlo para partidas completas de Yahtzee.

FASE CREA. Cada partida usa un generador aleatorio nuevo, derivado de una
semilla maestra, y tarjetas vacías. Las partidas son independientes e
idénticamente distribuidas dada la pareja de estrategias. Con eso, la media
de los puntajes converge al valor esperado de cada política cuando N crece
(Ley de los Grandes Números).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.random import Generator

from src.game import Game
from src.player import Player, Strategy, make_strategy
from src.scorecard import ALL_CATEGORIES


@dataclass
class PlayerStats:
    name: str
    strategy: str
    strategy_label: str
    totals: np.ndarray
    upper_subtotals: np.ndarray
    upper_bonuses: np.ndarray
    lower_subtotals: np.ndarray
    yahtzee_bonus_points: np.ndarray
    yahtzee_bonuses: np.ndarray
    yahtzees_rolled: np.ndarray
    categories: dict[str, np.ndarray]


@dataclass
class SimulationResult:
    n_games: int
    seed: int
    strategy_one: str
    strategy_two: str
    players: list[PlayerStats]
    winners: list[str]


class Simulator:
    """Ejecuta N partidas de dos jugadores y acumula sus puntajes."""

    def __init__(
        self,
        n_games: int,
        strategy_one: str | type[Strategy] | Strategy,
        strategy_two: str | type[Strategy] | Strategy,
        seed: int = 42,
        *,
        name_one: str = "Jugador 1",
        name_two: str = "Jugador 2",
        sims_per_mask: int = 24,
    ) -> None:
        if n_games < 1:
            raise ValueError("El número de partidas debe ser positivo.")
        self.n_games = n_games
        self.seed = seed
        self.name_one = name_one
        self.name_two = name_two
        self._strategy_one = _materialize(strategy_one, sims_per_mask)
        self._strategy_two = _materialize(strategy_two, sims_per_mask)

    def run(self, progress_every: int = 0) -> SimulationResult:
        master: Generator = np.random.default_rng(self.seed)
        totals = [np.empty(self.n_games, dtype=np.int32) for _ in range(2)]
        upper = [np.empty(self.n_games, dtype=np.int32) for _ in range(2)]
        upper_bonus = [np.empty(self.n_games, dtype=np.int32) for _ in range(2)]
        lower = [np.empty(self.n_games, dtype=np.int32) for _ in range(2)]
        yahtzee_bonus = [np.empty(self.n_games, dtype=np.int32) for _ in range(2)]
        yahtzee_bonus_count = [np.empty(self.n_games, dtype=np.int16) for _ in range(2)]
        yahtzees_rolled = [np.empty(self.n_games, dtype=np.int16) for _ in range(2)]
        categories = [
            {category: np.empty(self.n_games, dtype=np.int16) for category in ALL_CATEGORIES}
            for _ in range(2)
        ]
        winners: list[str] = []

        for index in range(self.n_games):
            game_seed = int(master.integers(0, np.iinfo(np.int64).max))
            game_rng = np.random.default_rng(game_seed)
            players = (
                Player(self.name_one, self._strategy_one),
                Player(self.name_two, self._strategy_two),
            )
            result = Game(players[0], players[1], game_rng).play()
            winners.append(result.winner)
            for slot, summary in enumerate(result.players):
                totals[slot][index] = int(summary["total"])
                upper[slot][index] = int(summary["upper_subtotal"])
                upper_bonus[slot][index] = int(summary["upper_bonus"])
                lower[slot][index] = int(summary["lower_subtotal"])
                yahtzee_bonus[slot][index] = int(summary["yahtzee_bonus_points"])
                yahtzee_bonus_count[slot][index] = int(summary["yahtzee_bonuses"])
                yahtzees_rolled[slot][index] = int(summary["yahtzees_rolled"])
                stored = summary["categories"]
                for category in ALL_CATEGORIES:
                    categories[slot][category][index] = int(stored[category])
            if progress_every and (index + 1) % progress_every == 0:
                print(f"  {index + 1}/{self.n_games} partidas", flush=True)

        labels = [self._strategy_one.label, self._strategy_two.label]
        names = [self.name_one, self.name_two]
        keys = [self._strategy_one.name, self._strategy_two.name]
        player_stats = [
            PlayerStats(
                name=names[slot],
                strategy=keys[slot],
                strategy_label=labels[slot],
                totals=totals[slot],
                upper_subtotals=upper[slot],
                upper_bonuses=upper_bonus[slot],
                lower_subtotals=lower[slot],
                yahtzee_bonus_points=yahtzee_bonus[slot],
                yahtzee_bonuses=yahtzee_bonus_count[slot],
                yahtzees_rolled=yahtzees_rolled[slot],
                categories=categories[slot],
            )
            for slot in range(2)
        ]
        return SimulationResult(
            n_games=self.n_games,
            seed=self.seed,
            strategy_one=keys[0],
            strategy_two=keys[1],
            players=player_stats,
            winners=winners,
        )


def _materialize(
    strategy: str | type[Strategy] | Strategy,
    sims_per_mask: int,
) -> Strategy:
    if isinstance(strategy, Strategy):
        return strategy
    if isinstance(strategy, str):
        return make_strategy(strategy, sims_per_mask)
    if isinstance(strategy, type) and issubclass(strategy, Strategy):
        return make_strategy(strategy.name, sims_per_mask) if hasattr(strategy, "name") else strategy()
    raise TypeError(f"No se reconoce la estrategia: {strategy!r}")
