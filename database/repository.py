"""
database/repository.py

Persists pipeline results to the database.

Single entry point: save_pipeline_results()
Creates anonymous Player records for each confirmed track (keyed by track_id)
then writes one PlayerMatchStats row per player.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from loguru import logger

from typing import Protocol, runtime_checkable

from database.models import Match, Player, PlayerMatchStats
from metrics.physical import PhysicalMetrics


# ---------------------------------------------------------------------------
# Protocol — avoids importing the full CV stack (torch, YOLO, etc.)
# ---------------------------------------------------------------------------

@runtime_checkable
class PressStatsLike(Protocol):
    """Structural type for PlayerPressStats — no CV imports required."""
    press_count: int
    press_success_rate: float
    trigger_accuracy: float


# ---------------------------------------------------------------------------
# Input container
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """
    All metric outputs from one pipeline run, ready to be persisted.

    Fields:
        match_id:               UUID of the Match record in the DB
        fps:                    source video frame rate
        physical_metrics:       track_id → PhysicalMetrics
        pitch_control_by_track: track_id → mean pitch control contribution [0, 1]
        press_stats:            track_id → PressStatsLike (may be partial)
        track_teams:            track_id → "home" | "away" | None
    """
    match_id: uuid.UUID
    fps: float
    physical_metrics: dict[int, PhysicalMetrics]
    pitch_control_by_track: dict[int, float]
    press_stats: dict[int, PressStatsLike]
    track_teams: dict[int, Optional[str]]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_pipeline_results(
    session: Session,
    academy_id: uuid.UUID,
    result: PipelineResult,
) -> int:
    """
    Persist all pipeline metrics for a match.

    For each track in result.physical_metrics:
    - Creates an anonymous Player record if one does not yet exist for
      (academy_id, track_id). Uses track_id as a stable external identifier
      stored in jersey_number for now; a future step links these to real
      player profiles via jersey OCR + manual confirmation.
    - Creates one PlayerMatchStats row with all available metrics.

    Updates Match.processing_status to "done".

    Returns the number of PlayerMatchStats rows created.
    """
    match = session.get(Match, result.match_id)
    if match is None:
        raise ValueError(f"Match {result.match_id} not found in database")

    rows_created = 0

    for track_id, physical in result.physical_metrics.items():
        player = _get_or_create_player(session, academy_id, track_id)
        press  = result.press_stats.get(track_id)
        pc     = result.pitch_control_by_track.get(track_id)
        team   = result.track_teams.get(track_id)

        stats = PlayerMatchStats(
            player_id=player.id,
            match_id=result.match_id,
            team=team or "unknown",
            # Physical
            top_speed_ms=physical.top_speed_ms,
            avg_speed_ms=physical.avg_speed_ms,
            distance_covered_m=physical.distance_covered_m,
            hi_run_count=physical.hi_run_count,
            sprint_count=physical.sprint_count,
            # Pressing
            press_count=press.press_count if press else 0,
            press_success_rate=press.press_success_rate if press else 0.0,
            press_trigger_accuracy=press.trigger_accuracy if press else 0.0,
            # Spatial
            pitch_control_contribution=pc,
        )
        session.add(stats)
        rows_created += 1

    match.processing_status = "done"
    session.flush()

    logger.info(
        f"Saved {rows_created} player stats rows for match {result.match_id}"
    )
    return rows_created


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_player(
    session: Session,
    academy_id: uuid.UUID,
    track_id: int,
) -> Player:
    """
    Return an existing Player for this track, or create an anonymous one.

    Anonymous players use track_id as jersey_number and position="unknown"
    until a human or OCR step links them to a real profile.
    """
    existing = session.execute(
        select(Player).where(
            Player.academy_id == academy_id,
            Player.jersey_number == track_id,
            Player.name == f"Track {track_id}",
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    player = Player(
        academy_id=academy_id,
        name=f"Track {track_id}",
        position="unknown",
        jersey_number=track_id,
    )
    session.add(player)
    session.flush()
    return player
