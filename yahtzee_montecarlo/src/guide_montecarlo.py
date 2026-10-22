"""Decisión de bloqueo tomada de la guía ``simulacion_01.ipynb``.

USA. El cuaderno del profesor no elige los dados con reglas fijas. Genera las
32 máscaras de un conjunto de cinco dados, y para cada máscara estima por
Montecarlo el puntaje de la mejor categoría si se relanzan los dados libres.
Se conserva la máscara de mayor valor esperado. Es una aproximación de un
paso: durante la simulación la máscara no vuelve a cambiar.

MODIFICA. Sobre ese procedimiento se corrigen tres puntos del cuaderno:

- Con un solo relanzamiento pendiente, la guía evalúa todas las máscaras sin
  tirar (resta uno al número de lanzamientos y llega a cero). Todas valen lo
  mismo y el código se queda con la primera, que suelta los cinco dados.
  Aquí ese relanzamiento sí se simula. Si ninguna máscara supera el puntaje
  de plantarse, el turno termina.
- Repetir el relanzamiento con la misma máscara no cambia la distribución:
  solo importa la última tirada. Cada simulación hace una muestra.
- El puntaje de la muestra usa la tarjeta de este proyecto, con bonus
  superior y comodín de Yahtzee. La guía sumaba las casillas y no aplicaba
  esos bonuses. El generador es el de la partida, no ``random`` global.
"""

from __future__ import annotations

from collections.abc import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import Generator

from src.player import Strategy
from src.scorecard import ALL_CATEGORIES, Scorecard, raw_score

# Una máscara por entero de 0 a 31. El bit i conserva el dado i.
KEEP_MASKS: tuple[tuple[int, ...], ...] = tuple(
    tuple(index for index in range(5) if (mask >> index) & 1)
    for mask in range(32)
)

# Orden de categorías del cuaderno, traducido a los nombres de este proyecto.
# Sirve de desempate, igual que en ``best_category_score`` de la guía.
GUIDE_CATEGORY_ORDER: tuple[str, ...] = ALL_CATEGORIES


def best_immediate_score(card: Scorecard, dice: list[int]) -> int:
    """Mayor puntaje legal ahora mismo. Es el criterio con el que cierra la guía."""
    options = card.legal_categories(dice)
    if not options:
        return 0
    return max(card.points_for(category, dice) for category in options)


def expected_score_for_hold(
    dice: list[int],
    hold: tuple[int, ...] | set[int],
    sims: int,
    rng: Generator,
    score_of: Callable[[list[int]], float],
) -> float:
    """Media del puntaje si los dados no conservados se relanzan una vez.

    Con la máscara fija, relanzar varias veces y quedarse con la última tiene
    la misma distribución que relanzar una sola vez.
    """
    held = set(hold)
    if len(held) == 5 or sims <= 0:
        return float(score_of(list(dice)))
    free = [index for index in range(5) if index not in held]
    rolls = rng.integers(1, 7, size=(sims, len(free)))
    total = 0.0
    trial = list(dice)
    for sample in range(sims):
        for offset, index in enumerate(free):
            trial[index] = int(rolls[sample, offset])
        total += score_of(trial)
    return total / sims


def choose_hold_montecarlo(
    dice: list[int],
    card: Scorecard,
    rng: Generator,
    sims_per_mask: int,
) -> set[int] | None:
    """Máscara de mayor valor esperado, o ``None`` para plantarse."""
    def score_of(trial: list[int]) -> float:
        return float(best_immediate_score(card, trial))

    stand = score_of(list(dice))
    best_ev = stand
    best_hold: set[int] | None = None
    for hold in KEEP_MASKS:
        if len(hold) == 5:
            continue
        estimated = expected_score_for_hold(dice, hold, sims_per_mask, rng, score_of)
        if estimated > best_ev:
            best_ev = estimated
            best_hold = set(hold)
    return best_hold


def choose_category_like_guide(dice: list[int], card: Scorecard) -> str:
    """Casilla legal de más puntos. El empate favorece el orden de la guía."""
    options = card.legal_categories(dice)

    def sort_key(category: str) -> tuple[int, int]:
        return (card.points_for(category, dice), -GUIDE_CATEGORY_ORDER.index(category))

    return max(options, key=sort_key)


class MonteCarloStrategy(Strategy):
    """FASE USA + MODIFICA. Bloqueo por Montecarlo, como en el cuaderno."""

    name = "montecarlo"
    label = "Montecarlo (guía)"

    def __init__(self, sims_per_mask: int = 24) -> None:
        if sims_per_mask < 1:
            raise ValueError("Las simulaciones por máscara deben ser al menos 1.")
        self.sims_per_mask = sims_per_mask

    def choose_hold(self, dice, roll_number, card, rng):
        return choose_hold_montecarlo(dice, card, rng, self.sims_per_mask)

    def choose_category(self, dice, card, rng):
        return choose_category_like_guide(dice, card)


def guide_ev_convergence(
    iterations: tuple[int, ...] = (10, 50, 100, 500, 1000, 5000, 10000),
    seed: int = 42,
) -> list[dict[str, float | int]]:
    """Réplica del experimento de convergencia del cuaderno.

    Dados [3, 3, 5, 2, 6], se conservan los dos treses y se estima el valor
    esperado de la mejor categoría entre treses, full, trío y chance.
    La guía hacía lo mismo con ``simulate_expected_value_after_keeps``.
    """
    dice = [3, 3, 5, 2, 6]
    hold = (0, 1)
    categories = ("threes", "full_house", "three_of_a_kind", "chance")
    rng = np.random.default_rng(seed)

    def score_of(trial: list[int]) -> float:
        return float(max(raw_score(category, trial) for category in categories))

    rows: list[dict[str, float | int]] = []
    for sims in iterations:
        estimated = expected_score_for_hold(dice, hold, sims, rng, score_of)
        rows.append({"iteraciones": sims, "valor_esperado": estimated})
    return rows


def plot_guide_ev_convergence(path, seed: int = 42) -> list[dict[str, float | int]]:
    """Guarda la convergencia del valor esperado de la máscara de ejemplo."""
    rows = guide_ev_convergence(seed=seed)
    figure, axis = plt.subplots(figsize=(8.6, 5.0))
    xs = [int(row["iteraciones"]) for row in rows]
    ys = [float(row["valor_esperado"]) for row in rows]
    axis.plot(xs, ys, marker="o", color="#0072B2", linewidth=1.8)
    axis.axhline(ys[-1], color="#D55E00", linestyle="--", linewidth=1.0, label=f"Referencia en N = {xs[-1]}: {ys[-1]:.2f}")
    axis.set_xscale("log")
    axis.set_title("Convergencia del valor esperado de una máscara\n(experimento de la guía, Ley de los Grandes Números)")
    axis.set_xlabel("Simulaciones de la máscara (escala logarítmica)")
    axis.set_ylabel("Valor esperado estimado")
    axis.grid(True, which="both", alpha=0.3)
    axis.legend(frameon=False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=140)
    plt.close(figure)
    return rows
