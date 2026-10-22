"""Pruebas de la fase USA: puntuación, bonus superior y Yahtzee adicional."""

import pytest

from src.scorecard import Scorecard, raw_score


@pytest.mark.parametrize(
    ("category", "dice", "expected"),
    [
        ("ones", [1, 1, 2, 3, 4], 2),
        ("sixes", [6, 6, 6, 1, 2], 18),
        ("three_of_a_kind", [5, 5, 5, 1, 2], 18),
        ("three_of_a_kind", [5, 5, 4, 1, 2], 0),
        ("four_of_a_kind", [6, 6, 6, 6, 2], 26),
        ("four_of_a_kind", [6, 6, 6, 6, 6], 30),
        ("full_house", [1, 1, 1, 2, 2], 25),
        ("full_house", [6, 6, 6, 6, 6], 0),
        ("small_straight", [1, 2, 3, 4, 6], 30),
        ("small_straight", [1, 2, 2, 3, 4], 30),
        ("small_straight", [1, 2, 3, 5, 6], 0),
        ("large_straight", [1, 2, 3, 4, 5], 40),
        ("large_straight", [2, 3, 4, 5, 6], 40),
        ("large_straight", [1, 2, 3, 4, 6], 0),
        ("yahtzee", [4, 4, 4, 4, 4], 50),
        ("yahtzee", [4, 4, 4, 4, 5], 0),
        ("chance", [1, 2, 3, 4, 6], 16),
    ],
)
def test_raw_scores(category, dice, expected):
    assert raw_score(category, dice) == expected


def test_upper_bonus_threshold():
    card = Scorecard()
    # Tres dados de cada número suman exactamente 63.
    for category, face in (
        ("ones", 1),
        ("twos", 2),
        ("threes", 3),
        ("fours", 4),
        ("fives", 5),
        ("sixes", 6),
    ):
        filler = (3, 4) if face < 3 else (1, 2)
        card.assign(category, [face, face, face, filler[0], filler[1]])
    assert card.upper_subtotal() == 63
    assert card.upper_bonus() == 35

    short = Scorecard()
    short.assign("ones", [1, 1, 3, 4, 5])
    short.assign("twos", [2, 2, 2, 1, 3])
    short.assign("threes", [3, 3, 3, 1, 2])
    short.assign("fours", [4, 4, 4, 1, 2])
    short.assign("fives", [5, 5, 5, 1, 2])
    short.assign("sixes", [6, 6, 6, 1, 2])
    assert short.upper_subtotal() == 62
    assert short.upper_bonus() == 0


def test_first_yahtzee_scores_50_without_bonus():
    card = Scorecard()
    assert card.assign("yahtzee", [3, 3, 3, 3, 3]) == 50
    assert card.yahtzee_bonuses == 0
    assert card.total() == 50


def test_extra_yahtzee_forces_upper_box_and_adds_100():
    card = Scorecard()
    card.assign("yahtzee", [2, 2, 2, 2, 2])
    dice = [6, 6, 6, 6, 6]
    assert card.legal_categories(dice) == ["sixes"]
    assert card.assign("sixes", dice) == 30
    assert card.yahtzee_bonuses == 1
    assert card.yahtzee_bonus_points() == 100
    assert card.total() == 50 + 30 + 100


def test_joker_scores_lower_categories_when_upper_is_closed():
    card = Scorecard()
    card.assign("yahtzee", [1, 1, 1, 1, 1])
    card.assign("sixes", [6, 6, 6, 1, 1])
    dice = [6, 6, 6, 6, 6]
    options = card.legal_categories(dice)
    assert "sixes" not in options
    assert "yahtzee" not in options
    assert "full_house" in options
    assert card.points_for("full_house", dice) == 25
    assert card.points_for("small_straight", dice) == 30
    assert card.points_for("large_straight", dice) == 40
    assert card.points_for("three_of_a_kind", dice) == 30
    card.assign("full_house", dice)
    assert card.scores["full_house"] == 25
    assert card.yahtzee_bonuses == 1


def test_zeroed_yahtzee_keeps_joker_but_not_the_100_bonus():
    card = Scorecard()
    card.assign("yahtzee", [1, 2, 3, 4, 5])
    assert card.scores["yahtzee"] == 0
    dice = [6, 6, 6, 6, 6]
    assert card.legal_categories(dice) == ["sixes"]
    assert card.assign("sixes", dice) == 30
    assert card.yahtzee_bonuses == 0


def test_joker_zeros_another_upper_box_when_lower_section_is_full():
    card = Scorecard()
    card.assign("yahtzee", [5, 5, 5, 5, 5])
    card.assign("sixes", [6, 1, 1, 1, 1])
    for category, dice in (
        ("three_of_a_kind", [4, 4, 4, 1, 1]),
        ("four_of_a_kind", [3, 3, 3, 3, 1]),
        ("full_house", [2, 2, 2, 1, 1]),
        ("small_straight", [1, 2, 3, 4, 6]),
        ("large_straight", [1, 2, 3, 4, 5]),
        ("chance", [6, 5, 4, 3, 2]),
    ):
        card.assign(category, dice)
    dice = [6, 6, 6, 6, 6]
    assert card.legal_categories(dice) == ["ones", "twos", "threes", "fours", "fives"]
    assert card.assign("ones", dice) == 0
    assert card.yahtzee_bonuses == 1


def test_closed_or_illegal_category_is_rejected():
    card = Scorecard()
    card.assign("chance", [1, 2, 3, 4, 5])
    with pytest.raises(ValueError):
        card.assign("chance", [2, 2, 2, 2, 2])
    card.assign("yahtzee", [2, 2, 2, 2, 2])
    with pytest.raises(ValueError):
        card.assign("ones", [6, 6, 6, 6, 6])


def test_total_matches_its_components():
    card = Scorecard()
    card.assign("ones", [1, 1, 1, 4, 5])
    card.assign("chance", [6, 5, 4, 3, 2])
    card.assign("yahtzee", [6, 6, 6, 6, 6])
    assert card.total() == (
        card.upper_subtotal()
        + card.upper_bonus()
        + card.lower_subtotal()
        + card.yahtzee_bonus_points()
    )
