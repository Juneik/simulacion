"""Pruebas de la fase USA: lanzamiento y conservación de dados."""

import numpy as np
import pytest

from src.dice import DiceSet


def test_roll_returns_five_faces():
    dice = DiceSet(np.random.default_rng(1))
    values = dice.roll_all()
    assert len(values) == 5
    assert all(1 <= value <= 6 for value in values)


def test_reroll_keeps_held_dice():
    dice = DiceSet(np.random.default_rng(2))
    first = dice.roll_all()
    second = dice.reroll({0, 2, 4})
    assert second[0] == first[0]
    assert second[2] == first[2]
    assert second[4] == first[4]
    assert len(second) == 5


def test_reroll_rejects_unknown_index():
    dice = DiceSet(np.random.default_rng(3))
    dice.roll_all()
    with pytest.raises(IndexError):
        dice.reroll({5})


def test_roll_all_replaces_previous_values():
    dice = DiceSet(np.random.default_rng(4))
    dice.roll_all()
    dice.reroll({0, 1, 2, 3, 4})
    again = dice.roll_all()
    assert len(again) == 5
