"""Pure rules for the basketball shooting minigame.

No purchases, wagering, monetary rewards or real-game predictions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShotResult:
    made: bool
    points: int
    xp: int


def attempt_shot(shot_type: int, roll: int) -> ShotResult:
    """Resolve a 2/3-point shot using an integer random roll from 0 to 99."""
    if shot_type not in (2, 3):
        raise ValueError("shot_type must be 2 or 3")
    if not 0 <= roll <= 99:
        raise ValueError("roll must be between 0 and 99")

    chance = 65 if shot_type == 2 else 35
    made = roll < chance
    return ShotResult(made=made, points=shot_type if made else 0, xp=5 if made else 1)
