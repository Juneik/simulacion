"""La estrategia Montecarlo conserva el procedimiento de la guía y corrige el último relanzamiento."""

import numpy as np

from src.guide_montecarlo import KEEP_MASKS, choose_hold_montecarlo
from src.scorecard import Scorecard
from src.simulator import Simulator


def test_there_are_32_keep_masks():
    assert len(KEEP_MASKS) == 32
    assert () in KEEP_MASKS
    assert tuple(range(5)) in KEEP_MASKS


def test_a_finished_yahtzee_stands_instead_of_rerolling():
    card = Scorecard()
    decision = choose_hold_montecarlo(
        [6, 6, 6, 6, 6],
        card,
        np.random.default_rng(1),
        sims_per_mask=12,
    )
    assert decision is None


def test_montecarlo_player_finishes_a_game():
    result = Simulator(2, "montecarlo", "avida", seed=3, sims_per_mask=4).run()
    assert result.players[0].strategy == "montecarlo"
    assert result.players[0].totals.shape == (2,)
    assert int(result.players[0].categories["chance"][0]) >= 0
