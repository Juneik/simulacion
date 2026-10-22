"""Punto de entrada: partida de demostración, simulación y análisis.

FASE USA: ``--demo`` juega una partida con las reglas completas.
FASE MODIFICA: ``--estrategia-1`` y ``--estrategia-2`` eligen la política.
FASE CREA: sin ``--demo``, el motor repite la partida N veces, exporta
CSV/JSON y guarda las gráficas de convergencia.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from src.analysis import build_summary, export_csv, export_json, format_summary, write_figures
from src.game import Game, render_game
from src.guide_montecarlo import plot_guide_ev_convergence
from src.player import STRATEGIES, Player, make_strategy
from src.simulator import Simulator

ROOT = Path(__file__).resolve().parent
DEFAULT_PAIRS = (
    ("aleatoria", "avida"),
    ("avida", "seccion_superior"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulación de Yahtzee clásico con el método de Montecarlo."
    )
    parser.add_argument("--partidas", "-n", type=int, default=5000, help="Número de partidas (por pareja de estrategias).")
    parser.add_argument("--estrategia-1", default="aleatoria", help="Estrategia del jugador 1.")
    parser.add_argument("--estrategia-2", default="avida", help="Estrategia del jugador 2.")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla del generador aleatorio.")
    parser.add_argument(
        "--salida",
        type=Path,
        default=ROOT / "results",
        help="Directorio de CSV, JSON y gráficas.",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Compara aleatoria vs ávida y ávida vs sección superior.",
    )
    parser.add_argument("--demo", action="store_true", help="Muestra una sola partida, turno a turno.")
    parser.add_argument("--sin-graficas", action="store_true", help="No genera archivos PNG.")
    parser.add_argument(
        "--progreso",
        type=int,
        default=1000,
        help="Imprime avance cada tantas partidas. Use 0 para silenciarlo.",
    )
    parser.add_argument(
        "--sims-mascara",
        type=int,
        default=24,
        help="Simulaciones por máscara de la estrategia montecarlo (guía del profesor).",
    )
    parser.add_argument(
        "--convergencia-guia",
        action="store_true",
        help="Replica el experimento de convergencia del valor esperado del cuaderno.",
    )
    parser.add_argument(
        "--estrategias",
        action="store_true",
        help="Lista las estrategias disponibles y termina.",
    )
    return parser.parse_args(argv)


def play_demo(strategy_one: str, strategy_two: str, seed: int, sims_per_mask: int) -> None:
    rng = np.random.default_rng(seed)
    game = Game(
        Player("Jugador 1", make_strategy(strategy_one, sims_per_mask)),
        Player("Jugador 2", make_strategy(strategy_two, sims_per_mask)),
        rng,
        record_turns=True,
    )
    print(f"Partida de demostración (semilla {seed})")
    print(render_game(game.play()))


def run_pair(
    strategy_one: str,
    strategy_two: str,
    n_games: int,
    seed: int,
    output: Path,
    *,
    figures: bool,
    progress_every: int,
    sims_per_mask: int,
) -> dict:
    print(f"\nSimulando {n_games} partidas: {strategy_one} vs {strategy_two}")
    result = Simulator(
        n_games, strategy_one, strategy_two, seed, sims_per_mask=sims_per_mask
    ).run(progress_every)
    summary = build_summary(result)
    output.mkdir(parents=True, exist_ok=True)
    export_json(summary, output / "resumen.json")
    export_csv(result, output / "partidas.csv")
    if figures:
        write_figures(result, output)
    print(format_summary(summary))
    print(f"Resultados en: {output}")
    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.estrategias:
        for key, cls in STRATEGIES.items():
            print(f"{key:<20} {cls.label}")
        return 0
    if args.partidas < 1:
        print("El número de partidas debe ser positivo.", file=sys.stderr)
        return 2
    if args.convergencia_guia:
        destination = args.salida / "convergencia_ev_guia.png"
        rows = plot_guide_ev_convergence(destination, seed=args.semilla)
        print("Convergencia del valor esperado (experimento de la guía)")
        for row in rows:
            print(f"  N = {int(row['iteraciones']):6d}    EV = {float(row['valor_esperado']):.3f}")
        print(f"Gráfica: {destination}")
        return 0
    if args.demo:
        play_demo(args.estrategia_1, args.estrategia_2, args.semilla, args.sims_mascara)
        return 0

    if args.suite:
        combined = []
        for index, pair in enumerate(DEFAULT_PAIRS):
            folder = args.salida / f"{pair[0]}_vs_{pair[1]}"
            summary = run_pair(
                pair[0],
                pair[1],
                args.partidas,
                args.semilla + index,
                folder,
                figures=not args.sin_graficas,
                progress_every=args.progreso,
                sims_per_mask=args.sims_mascara,
            )
            combined.append(summary)
        args.salida.mkdir(parents=True, exist_ok=True)
        suite_path = args.salida / "suite_resumen.json"
        suite_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResumen combinado: {suite_path}")
        return 0

    run_pair(
        args.estrategia_1,
        args.estrategia_2,
        args.partidas,
        args.semilla,
        args.salida,
        figures=not args.sin_graficas,
        progress_every=args.progreso,
        sims_per_mask=args.sims_mascara,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
