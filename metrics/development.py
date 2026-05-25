"""
metrics/development.py

Computes a DevelopmentScore from one PlayerMatchStats row.

All sub-scores are in [0, 10]. Normalisation bounds are based on
typical academy-level performance ranges; clip to [0, 10].
"""

from __future__ import annotations
from typing import Optional


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _norm(value: float, lo: float, hi: float) -> float:
    """Map value from [lo, hi] → [0, 10], clipped."""
    return max(0.0, min(10.0, (value - lo) / (hi - lo) * 10.0))


def _mean(values: list[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


# ---------------------------------------------------------------------------
# Sub-score functions
# ---------------------------------------------------------------------------

def _physical(stats) -> Optional[float]:
    subs = []
    if stats.distance_covered_m is not None:
        subs.append(_norm(stats.distance_covered_m, 5_000, 12_000))
    if stats.sprint_count is not None:
        subs.append(_norm(stats.sprint_count, 0, 30))
    if stats.hi_run_count is not None:
        subs.append(_norm(stats.hi_run_count, 0, 50))
    if stats.top_speed_ms is not None:
        subs.append(_norm(stats.top_speed_ms, 5.0, 9.0))
    return _mean(subs)


def _tactical(stats) -> Optional[float]:
    subs = []
    if stats.pitch_control_contribution is not None:
        # 15% control = elite for one player on a field of 22
        subs.append(_norm(stats.pitch_control_contribution, 0.0, 0.15))
    if stats.press_success_rate is not None:
        subs.append(_norm(stats.press_success_rate, 0.0, 1.0))
    return _mean(subs)


def _technical(stats) -> Optional[float]:
    subs = []
    if stats.press_trigger_accuracy is not None:
        subs.append(_norm(stats.press_trigger_accuracy, 0.0, 1.0))
    return _mean(subs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_development_score(stats) -> dict:
    """
    Derive physical / tactical / technical / overall scores from a
    PlayerMatchStats object (or any object with the same attributes).

    Returns a dict with keys:
        physical_score, tactical_score, technical_score, overall_score

    Sub-scores that cannot be computed (all inputs None) are returned as None
    and are excluded from the overall weighted average.
    """
    physical  = _physical(stats)
    tactical  = _tactical(stats)
    technical = _technical(stats)

    # Weighted average over available sub-scores only
    weights = {
        "physical":  (physical,  0.40),
        "tactical":  (tactical,  0.35),
        "technical": (technical, 0.25),
    }
    weighted_sum = sum(score * w for score, w in weights.values() if score is not None)
    total_weight = sum(w for score, w in weights.values() if score is not None)
    overall = weighted_sum / total_weight if total_weight > 0 else 0.0

    return {
        "physical_score":  physical,
        "tactical_score":  tactical,
        "technical_score": technical,
        "overall_score":   overall,
    }
