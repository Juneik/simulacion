"""Pruebas de partida completa, estrategias y reproducibilidad."""

import numpy as np

from src.game import Game
from src.player import Player, resolve_strategy
from src.scorecard import ALL_CATEGORIES
from src.simulator import Simulator


def _play(strategy_one: str, strategy_two: str, seed: int, record: bool = False):
    rng = np.random.default_rng(seed)
    game = Game(
        Player("Jugador 1", resolve_strategy(strategy_one)()),
        Player("Jugador 2", resolve_strategy(strategy_two)()),
        rng,
        record_turns=record,
    )
    return game.play()


def test_game_fills_every_category_and_reconciles_the_total():
    result = _play("aleatoria", "avida", seed=7, record=True)
    assert len(result.turns) == 26
    for player in result.players:
        categories = player["categories"]
        assert all(categories[name] is not None for name in ALL_CATEGORIES)
        assert player["total"] == (
            player["upper_subtotal"]
            + player["upper_bonus"]
            + player["lower_subtotal"]
            + player["yahtzee_bonus_points"]
        )
    scores = [player["total"] for player in result.players]
    if scores[0] == scores[1]:
        assert result.winner == "empate"
    else:
        winner_name = result.players[int(scores[1] > scores[0])]["name"]
        assert result.winner == winner_name


def test_same_seed_reproduces_the_game():
    first = _play("seccion_superior", "avida", seed=11)
    second = _play("seccion_superior", "avida", seed=11)
    assert first.players[0]["total"] == second.players[0]["total"]
    assert first.players[1]["categories"] == second.players[1]["categories"]


def test_strategies_finish_many_games_without_illegal_moves():
    for left, right in (("aleatoria", "aleatoria"), ("avida", "seccion_superior"), ("aleatoria", "seccion_superior")):
        result = Simulator(40, left, right, seed=5).run()
        assert result.n_games == 40
        for player in result.players:
            assert player.totals.shape == (40,)
            assert np.all(player.totals >= 0)


def test_unknown_strategy_is_reported():
    try:
        resolve_strategy("imposible")
    except KeyError as error:
        assert "imposible" in str(error)
    else:
        raise AssertionError("Se esperaba KeyError")
