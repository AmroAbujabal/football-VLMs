"""
metrics/physical.py

Computes per-player physical performance metrics from pitch-coordinate
position histories.

All functions are pure — no DB, no I/O, no GPU.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from config.settings import settings


@dataclass
class PhysicalMetrics:
    """Physical performance metrics for one player in one match."""
    track_id: int
    top_speed_ms: float
    avg_speed_ms: float
    distance_covered_m: float
    hi_run_count: int      # distinct bouts above high_intensity_speed threshold
    sprint_count: int      # distinct bouts above sprint_speed threshold


def compute_physical_metrics(
    track_id: int,
    pitch_positions: np.ndarray,   # (N, 2) in pitch metres
    fps: float = settings.default_fps,
    hi_speed_threshold: float = settings.high_intensity_speed,
    sprint_threshold: float = settings.sprint_speed,
) -> PhysicalMetrics:
    """
    Compute physical metrics from a sequence of pitch-coordinate positions.

    Args:
        track_id:           identifier for the player track
        pitch_positions:    (N, 2) array of (x, y) positions in metres
        fps:                frames per second of the source video
        hi_speed_threshold: m/s — minimum speed for a high-intensity run
        sprint_threshold:   m/s — minimum speed for a sprint

    Returns:
        PhysicalMetrics dataclass
    """
    n = len(pitch_positions)

    if n < 2:
        return PhysicalMetrics(
            track_id=track_id,
            top_speed_ms=0.0,
            avg_speed_ms=0.0,
            distance_covered_m=0.0,
            hi_run_count=0,
            sprint_count=0,
        )

    # Frame-to-frame distances in metres
    deltas = np.linalg.norm(np.diff(pitch_positions, axis=0), axis=1)  # (N-1,)

    # Speed at each interval in m/s
    speeds = deltas * fps  # (N-1,)

    distance   = float(deltas.sum())
    top_speed  = float(speeds.max())
    avg_speed  = float(speeds.mean())

    hi_run_count = _count_bouts(speeds, hi_speed_threshold)
    sprint_count  = _count_bouts(speeds, sprint_threshold)

    return PhysicalMetrics(
        track_id=track_id,
        top_speed_ms=top_speed,
        avg_speed_ms=avg_speed,
        distance_covered_m=distance,
        hi_run_count=hi_run_count,
        sprint_count=sprint_count,
    )


def _count_bouts(speeds: np.ndarray, threshold: float) -> int:
    """
    Count the number of distinct contiguous periods where speed > threshold.

    A new bout begins when speed crosses from ≤ threshold to > threshold.
    """
    above = speeds > threshold
    # Rising edges: False → True transitions
    bouts = int(np.sum(np.diff(above.astype(np.int8)) == 1))
    # If the sequence starts already above threshold, count that as a bout too
    if len(above) > 0 and above[0]:
        bouts += 1
    return bouts
