"""Una partida completa de Yahtzee entre dos jugadores.

FASE USA. Cada jugador dispone de trece turnos. En cada turno lanza cinco
dados hasta tres veces, conserva un subconjunto entre lanzamientos y cierra
exactamente una categoría. Gana quien termina con mayor puntaje total.
Los puntajes no interfieren entre sí: la partida es competitiva solo al
comparar los totales.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from numpy.random import Generator

from src.dice import DiceSet
from src.player import Player, format_category, format_dice
from src.scorecard import is_yahtzee


@dataclass
class TurnLog:
    player: str
    strategy: str
    rolls: list[list[int]]
    holds: list[list[int]]
    category: str
    points: int
    total_after: int
    yahtzee_rolled: bool


@dataclass
class GameResult:
    players: list[dict[str, object]]
    winner: str
    turns: list[TurnLog] = field(default_factory=list)


class Game:
    """Orquesta trece rondas en las que juegan, en orden, los dos jugadores."""

    def __init__(
        self,
        player_one: Player,
        player_two: Player,
        rng: Generator,
        *,
        record_turns: bool = False,
    ) -> None:
        self.players = (player_one, player_two)
        self.dice = DiceSet(rng)
        self.rng = rng
        self.record_turns = record_turns

    def play(self) -> GameResult:
        turns: list[TurnLog] = []
        for _round in range(13):
            for player in self.players:
                turn = self._play_turn(player)
                if self.record_turns:
                    turns.append(turn)
        totals = [player.scorecard.total() for player in self.players]
        if totals[0] > totals[1]:
            winner = self.players[0].name
        elif totals[1] > totals[0]:
            winner = self.players[1].name
        else:
            winner = "empate"
        return GameResult(
            players=[player.summary() for player in self.players],
            winner=winner,
            turns=turns,
        )

    def _play_turn(self, player: Player) -> TurnLog:
        rolls = [self.dice.roll_all()]
        holds: list[list[int]] = []
        for roll_number in (1, 2):
            decision = player.strategy.choose_hold(
                rolls[-1], roll_number, player.scorecard, self.rng
            )
            if decision is None or len(decision) == len(rolls[-1]):
                break
            holds.append(sorted(decision))
            rolls.append(self.dice.reroll(decision))

        final = rolls[-1]
        category = player.strategy.choose_category(final, player.scorecard, self.rng)
        points = player.scorecard.assign(category, final)
        rolled_yahtzee = is_yahtzee(final)
        if rolled_yahtzee:
            player.yahtzees_rolled += 1
        return TurnLog(
            player=player.name,
            strategy=player.strategy.name,
            rolls=rolls,
            holds=holds,
            category=category,
            points=points,
            total_after=player.scorecard.total(),
            yahtzee_rolled=rolled_yahtzee,
        )


def render_game(result: GameResult) -> str:
    """Texto legible de una partida registrada turno a turno."""
    lines: list[str] = []
    header = "  vs  ".join(
        f"{player['name']} ({player['strategy_label']})" for player in result.players
    )
    lines.append(header)
    lines.append("-" * len(header))
    played = {str(player["name"]): 0 for player in result.players}
    for turn in result.turns:
        played[turn.player] += 1
        lines.append("")
        lines.append(f"Turno {played[turn.player]} — {turn.player}")
        for roll_index, roll in enumerate(turn.rolls, start=1):
            lines.append(f"  Lanzamiento {roll_index}: {format_dice(roll)}")
            if roll_index - 1 < len(turn.holds):
                kept = [roll[index] for index in turn.holds[roll_index - 1]]
                lines.append(f"    Conserva: {format_dice(kept)}")
        yahtzee_mark = "  (Yahtzee)" if turn.yahtzee_rolled else ""
        lines.append(f"  Anota {format_category(turn.category)} = {turn.points}{yahtzee_mark}")
        lines.append(f"  Total parcial: {turn.total_after}")
    lines.append("")
    lines.append("Resultado final")
    for player in result.players:
        lines.append(
            f"  {player['name']} ({player['strategy_label']}): {player['total']} puntos "
            f"[superior {player['upper_subtotal']} + bonus {player['upper_bonus']} "
            f"+ inferior {player['lower_subtotal']} "
            f"+ Yahtzee extra {player['yahtzee_bonus_points']}]"
        )
    if result.winner == "empate":
        lines.append("  Empate.")
    else:
        lines.append(f"  Gana {result.winner}.")
    return "\n".join(lines)
