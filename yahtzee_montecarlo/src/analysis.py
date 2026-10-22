"""Estadísticos, exportación y gráficas de convergencia.

FASE CREA. A partir de las partidas i.i.d. del simulador se estiman medias,
desviaciones e intervalos de confianza, y se dibuja cómo la media acumulada
se acerca al nivel de equilibrio de cada estrategia.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.scorecard import ALL_CATEGORIES, CATEGORY_LABELS
from src.simulator import PlayerStats, SimulationResult

COLOR_ONE = "#0072B2"
COLOR_TWO = "#E69F00"
CHECKPOINTS = (50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000)


def describe(values: np.ndarray) -> dict[str, float | int]:
    """Media, dispersión e intervalo de confianza normal al 95 %."""
    sample = np.asarray(values, dtype=float)
    size = int(sample.size)
    mean = float(np.mean(sample))
    if size > 1:
        std = float(np.std(sample, ddof=1))
        standard_error = std / np.sqrt(size)
    else:
        std = 0.0
        standard_error = 0.0
    return {
        "n": size,
        "mean": mean,
        "std": std,
        "median": float(np.median(sample)),
        "min": int(np.min(sample)),
        "max": int(np.max(sample)),
        "ci95_low": mean - 1.96 * standard_error,
        "ci95_high": mean + 1.96 * standard_error,
    }


def running_mean(values: np.ndarray) -> np.ndarray:
    totals = np.cumsum(np.asarray(values, dtype=float))
    counts = np.arange(1, values.size + 1)
    return totals / counts


def _rate(mask: np.ndarray) -> float:
    return float(np.mean(mask)) if mask.size else 0.0


def player_report(player: PlayerStats) -> dict[str, object]:
    """Resumen serializable de un jugador a lo largo de las N partidas."""
    score = describe(player.totals)
    checkpoints = []
    means = running_mean(player.totals)
    for n in CHECKPOINTS:
        if n <= player.totals.size:
            checkpoints.append({"n": n, "running_mean": float(means[n - 1])})
    if not checkpoints or checkpoints[-1]["n"] != player.totals.size:
        checkpoints.append({"n": int(player.totals.size), "running_mean": float(means[-1])})

    categories = {}
    for category in ALL_CATEGORIES:
        column = player.categories[category]
        categories[category] = {
            "label": CATEGORY_LABELS[category],
            "mean": float(np.mean(column)),
            "positive_rate": _rate(column > 0),
        }
    return {
        "name": player.name,
        "strategy": player.strategy,
        "strategy_label": player.strategy_label,
        "score": score,
        "upper_subtotal_mean": float(np.mean(player.upper_subtotals)),
        "upper_bonus_rate": _rate(player.upper_bonuses > 0),
        "upper_bonus_mean": float(np.mean(player.upper_bonuses)),
        "lower_subtotal_mean": float(np.mean(player.lower_subtotals)),
        "yahtzee_bonus_mean": float(np.mean(player.yahtzee_bonus_points)),
        "yahtzee_bonus_rate": _rate(player.yahtzee_bonuses > 0),
        "mean_yahtzees_rolled": float(np.mean(player.yahtzees_rolled)),
        "yahtzee_scored_rate": categories["yahtzee"]["positive_rate"],
        "full_house_rate": _rate(player.categories["full_house"] == 25),
        "small_straight_rate": _rate(player.categories["small_straight"] == 30),
        "large_straight_rate": _rate(player.categories["large_straight"] == 40),
        "checkpoints": checkpoints,
        "categories": categories,
    }


def win_report(result: SimulationResult) -> dict[str, float | int]:
    winners = np.array(result.winners)
    size = max(len(winners), 1)
    return {
        "player_one_wins": int(np.sum(winners == result.players[0].name)),
        "player_two_wins": int(np.sum(winners == result.players[1].name)),
        "ties": int(np.sum(winners == "empate")),
        "player_one_win_rate": float(np.sum(winners == result.players[0].name) / size),
        "player_two_win_rate": float(np.sum(winners == result.players[1].name) / size),
        "tie_rate": float(np.sum(winners == "empate") / size),
    }


def build_summary(result: SimulationResult) -> dict[str, object]:
    return {
        "n_games": result.n_games,
        "seed": result.seed,
        "strategies": [result.strategy_one, result.strategy_two],
        "players": [player_report(player) for player in result.players],
        "wins": win_report(result),
    }


def export_json(summary: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def export_csv(result: SimulationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["partida", "ganador"]
    for slot, player in enumerate(result.players, start=1):
        prefix = f"j{slot}"
        fieldnames.extend(
            [
                f"{prefix}_estrategia",
                f"{prefix}_total",
                f"{prefix}_superior",
                f"{prefix}_bonus_superior",
                f"{prefix}_inferior",
                f"{prefix}_bonus_yahtzee",
                f"{prefix}_yahtzees",
            ]
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(result.n_games):
            row: dict[str, object] = {"partida": index + 1, "ganador": result.winners[index]}
            for slot, player in enumerate(result.players, start=1):
                prefix = f"j{slot}"
                row[f"{prefix}_estrategia"] = player.strategy
                row[f"{prefix}_total"] = int(player.totals[index])
                row[f"{prefix}_superior"] = int(player.upper_subtotals[index])
                row[f"{prefix}_bonus_superior"] = int(player.upper_bonuses[index])
                row[f"{prefix}_inferior"] = int(player.lower_subtotals[index])
                row[f"{prefix}_bonus_yahtzee"] = int(player.yahtzee_bonus_points[index])
                row[f"{prefix}_yahtzees"] = int(player.yahtzees_rolled[index])
            writer.writerow(row)


def _style_axis(axis: plt.Axes) -> None:
    axis.grid(True, alpha=0.3)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)


def plot_convergence(result: SimulationResult, path: Path) -> None:
    """Media acumulada frente a N, con la banda aproximada del 95 %."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9.2, 5.2))
    colors = (COLOR_ONE, COLOR_TWO)
    for player, color in zip(result.players, colors):
        means = running_mean(player.totals)
        ns = np.arange(1, result.n_games + 1)
        std = float(np.std(player.totals, ddof=1))
        band = 1.96 * std / np.sqrt(ns)
        final = float(means[-1])
        axis.plot(ns, means, color=color, linewidth=1.8, label=f"{player.strategy_label} (media {final:.1f})")
        axis.fill_between(ns, final - band, final + band, color=color, alpha=0.15)
        axis.axhline(final, color=color, linewidth=0.8, linestyle="--", alpha=0.8)
    axis.set_title("Convergencia del puntaje medio (Ley de los Grandes Números)")
    axis.set_xlabel("Número de partidas (N)")
    axis.set_ylabel("Puntaje medio acumulado")
    axis.legend(frameon=False)
    _style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=140)
    plt.close(figure)


def plot_deviation(result: SimulationResult, path: Path) -> None:
    """Distancia entre la media acumulada y la media final de la muestra."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9.2, 5.2))
    colors = (COLOR_ONE, COLOR_TWO)
    ns = np.arange(1, result.n_games + 1)
    for player, color in zip(result.players, colors):
        means = running_mean(player.totals)
        deviation = np.abs(means - means[-1])
        axis.plot(ns, deviation, color=color, linewidth=1.6, label=player.strategy_label)
    axis.set_title("Acercamiento de la media muestral a su valor de equilibrio")
    axis.set_xlabel("Número de partidas (N)")
    axis.set_ylabel("|Media acumulada − media final|")
    axis.legend(frameon=False)
    _style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=140)
    plt.close(figure)


def plot_histogram(result: SimulationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9.2, 5.2))
    colors = (COLOR_ONE, COLOR_TWO)
    combined = np.concatenate([player.totals for player in result.players])
    bins = np.linspace(float(combined.min()), float(combined.max()), 36)
    for player, color in zip(result.players, colors):
        axis.hist(
            player.totals,
            bins=bins,
            color=color,
            alpha=0.55,
            label=player.strategy_label,
            edgecolor="white",
            linewidth=0.4,
        )
    axis.set_title("Distribución de los puntajes finales")
    axis.set_xlabel("Puntaje final")
    axis.set_ylabel("Frecuencia")
    axis.legend(frameon=False)
    _style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=140)
    plt.close(figure)


def plot_comparison(result: SimulationResult, path: Path) -> None:
    """Componentes medios del puntaje y total con intervalo de confianza."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8.4, 5.2))
    labels = [player.strategy_label for player in result.players]
    components = (
        ("Sección superior", [float(np.mean(p.upper_subtotals)) for p in result.players], "#4C78A8"),
        ("Bonus superior", [float(np.mean(p.upper_bonuses)) for p in result.players], "#F58518"),
        ("Sección inferior", [float(np.mean(p.lower_subtotals)) for p in result.players], "#54A24B"),
        ("Bonus Yahtzee", [float(np.mean(p.yahtzee_bonus_points)) for p in result.players], "#E45756"),
    )
    x = np.arange(len(result.players))
    bottoms = np.zeros(len(result.players))
    for name, values, color in components:
        axis.bar(x, values, bottom=bottoms, color=color, width=0.62, label=name)
        bottoms = bottoms + np.asarray(values)
    for index, player in enumerate(result.players):
        stats = describe(player.totals)
        axis.errorbar(
            index,
            stats["mean"],
            yerr=[[stats["mean"] - stats["ci95_low"]], [stats["ci95_high"] - stats["mean"]]],
            fmt="o",
            color="black",
            capsize=4,
            label="Media e IC 95 %" if index == 0 else None,
        )
        axis.annotate(
            f"{stats['mean']:.1f}",
            (index, stats["mean"]),
            textcoords="offset points",
            xytext=(12, 6),
            ha="left",
            fontsize=9,
        )
    axis.set_xticks(x, labels)
    axis.set_ylabel("Puntos medios")
    axis.set_title("Comparación de estrategias por componente del puntaje")
    axis.legend(frameon=False, ncol=2)
    _style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=140)
    plt.close(figure)


def plot_categories(result: SimulationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10.4, 5.4))
    x = np.arange(len(ALL_CATEGORIES))
    width = 0.38
    colors = (COLOR_ONE, COLOR_TWO)
    for offset, player, color in zip((-width / 2, width / 2), result.players, colors):
        means = [float(np.mean(player.categories[category])) for category in ALL_CATEGORIES]
        axis.bar(x + offset, means, width=width, color=color, label=player.strategy_label)
    axis.set_xticks(x, [CATEGORY_LABELS[category] for category in ALL_CATEGORIES], rotation=40, ha="right")
    axis.set_ylabel("Puntos medios en la casilla")
    axis.set_title("Puntaje medio por categoría")
    axis.legend(frameon=False)
    _style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=140)
    plt.close(figure)


def write_figures(result: SimulationResult, directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "convergencia": directory / "convergencia.png",
        "desviacion": directory / "desviacion_lln.png",
        "histograma": directory / "histograma.png",
        "comparacion": directory / "comparacion_estrategias.png",
        "categorias": directory / "frecuencia_categorias.png",
    }
    plot_convergence(result, paths["convergencia"])
    plot_deviation(result, paths["desviacion"])
    plot_histogram(result, paths["histograma"])
    plot_comparison(result, paths["comparacion"])
    plot_categories(result, paths["categorias"])
    return paths


def format_summary(summary: dict[str, object]) -> str:
    """Tabla de texto para la consola y para transcribir al informe."""
    lines = [
        f"Partidas: {summary['n_games']}    Semilla: {summary['seed']}",
        "",
    ]
    header = (
        f"{'Estrategia':<20} {'Media':>8} {'DE':>8} {'IC 95 %':>22} "
        f"{'Bonus sup.':>12} {'Yahtzees':>10} {'Victorias':>10}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    wins = summary["wins"]
    rates = (wins["player_one_win_rate"], wins["player_two_win_rate"])
    for player, rate in zip(summary["players"], rates):
        score = player["score"]
        interval = f"[{score['ci95_low']:.1f}, {score['ci95_high']:.1f}]"
        lines.append(
            f"{player['strategy_label']:<20} {score['mean']:8.2f} {score['std']:8.2f} {interval:>22} "
            f"{100 * player['upper_bonus_rate']:11.1f}% {player['mean_yahtzees_rolled']:10.3f} {100 * rate:9.2f}%"
        )
    lines.append(
        f"Empates: {wins['ties']} ({100 * wins['tie_rate']:.1f}%)"
    )
    lines.append("")
    lines.append("Media acumulada en cortes de N:")
    for player in summary["players"]:
        pieces = [f"N={item['n']}: {item['running_mean']:.2f}" for item in player["checkpoints"]]
        lines.append(f"  {player['strategy_label']}: " + " | ".join(pieces))
    return "\n".join(lines)
