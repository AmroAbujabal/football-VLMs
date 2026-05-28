"""
metrics/features.py

Assembles per-player match history into feature vectors for the prediction model.

Public API:
    assemble_player_features(player_id, session, n_matches=8) -> list[dict]
    build_training_dataset(session, n_matches=4) -> (X: list[list], y: list[float])
    FEATURE_KEYS: tuple[str, ...] — ordered feature names (matches X column order)
"""

from __future__ import annotations

from datetime import timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import DevelopmentScore, Match, Player, PlayerMatchStats

FEATURE_KEYS: tuple[str, ...] = (
    "distance_covered_m",
    "sprint_count",
    "hi_run_count",
    "top_speed_ms",
    "press_success_rate",
    "pitch_control_contribution",
)


def assemble_player_features(
    player_id: UUID,
    session: Session,
    n_matches: int = 8,
) -> list[dict[str, Any]]:
    """
    Return up to n_matches most-recent feature rows for a player, oldest→newest.

    Each row is a dict with keys: match_date + all FEATURE_KEYS.
    Missing metric values are returned as None.
    """
    rows = session.execute(
        select(PlayerMatchStats, Match.match_date)
        .join(Match, PlayerMatchStats.match_id == Match.id)
        .where(PlayerMatchStats.player_id == player_id)
        .order_by(Match.match_date.desc())
        .limit(n_matches)
    ).all()

    result = []
    for stats, match_date in reversed(rows):
        result.append({
            "match_date": match_date,
            **{key: getattr(stats, key) for key in FEATURE_KEYS},
        })
    return result


def build_training_dataset(
    session: Session,
    n_matches: int = 4,
) -> tuple[list[list[float | None]], list[float]]:
    """
    Build (X, y) training arrays across all players.

    For each player with ≥2 matches:
      - features: the most recent (n_matches - 1) rows from assemble_player_features,
        flattened into a single vector
      - target: the overall_score from the DevelopmentScore for the week
        following the last feature match

    Players without a target DevelopmentScore in that week are skipped.
    Returns (X, y) where X is a list of flat feature lists and y is a list of floats.
    """
    X: list[list[float | None]] = []
    y: list[float] = []

    player_ids = session.execute(select(Player.id)).scalars().all()

    for player_id in player_ids:
        rows = assemble_player_features(player_id, session, n_matches=n_matches)
        if len(rows) < 2:
            continue

        feature_rows = rows[:-1]
        last_match_date = rows[-1]["match_date"]

        # Target: DevelopmentScore for the week containing or after last_match_date
        if last_match_date is None:
            continue

        last_dt = last_match_date if last_match_date.tzinfo else \
            last_match_date.replace(tzinfo=timezone.utc)
        week_start = last_dt - timedelta(days=last_dt.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        dev_score = session.execute(
            select(DevelopmentScore)
            .where(
                DevelopmentScore.player_id == player_id,
                DevelopmentScore.week_start >= week_start,
            )
            .order_by(DevelopmentScore.week_start.asc())
            .limit(1)
        ).scalar_one_or_none()

        if dev_score is None:
            continue

        flat = [row[key] for row in feature_rows for key in FEATURE_KEYS]
        X.append(flat)
        y.append(dev_score.overall_score)

    return X, y
