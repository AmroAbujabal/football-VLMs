"""
tests/test_metrics/test_physical.py

TDD tests for metrics/physical.py.
Pure-function tests — no DB, no video, no GPU required.

Run with: pytest tests/test_metrics/test_physical.py -v
"""

import numpy as np
import pytest

from metrics.physical import PhysicalMetrics, compute_physical_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def straight_line_positions(
    n_frames: int,
    speed_ms: float,
    fps: float,
    start: tuple[float, float] = (0.0, 0.0),
    direction: tuple[float, float] = (1.0, 0.0),
) -> np.ndarray:
    """
    Generate (N, 2) pitch positions for a player moving in a straight line
    at a constant speed.
    """
    step = speed_ms / fps
    positions = []
    x, y = start
    dx, dy = direction
    norm = (dx ** 2 + dy ** 2) ** 0.5
    dx, dy = dx / norm, dy / norm
    for _ in range(n_frames):
        positions.append([x, y])
        x += dx * step
        y += dy * step
    return np.array(positions, dtype=np.float64)


# ---------------------------------------------------------------------------
# PhysicalMetrics dataclass
# ---------------------------------------------------------------------------

class TestPhysicalMetricsDataclass:

    def test_has_required_fields(self):
        m = PhysicalMetrics(
            track_id=1,
            top_speed_ms=8.5,
            avg_speed_ms=4.2,
            distance_covered_m=1800.0,
            hi_run_count=12,
            sprint_count=4,
        )
        assert m.track_id == 1
        assert m.top_speed_ms == 8.5
        assert m.distance_covered_m == 1800.0


# ---------------------------------------------------------------------------
# compute_physical_metrics — distance
# ---------------------------------------------------------------------------

class TestDistanceCovered:

    def test_stationary_player_has_zero_distance(self):
        positions = np.zeros((100, 2))
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=25.0)
        assert m.distance_covered_m == pytest.approx(0.0, abs=0.01)

    def test_player_running_at_known_speed(self):
        fps = 25.0
        speed = 5.0          # m/s
        n_frames = 125       # 5 seconds
        positions = straight_line_positions(n_frames, speed, fps)
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        # 5 m/s × 5 s = 25 m (minus one frame step since distance is between positions)
        assert m.distance_covered_m == pytest.approx(24.0, abs=1.0)

    def test_distance_is_path_length_not_displacement(self):
        """A player who runs back and forth covers more than their displacement."""
        fps = 25.0
        half = straight_line_positions(50, 5.0, fps, direction=(1, 0))
        back = straight_line_positions(50, 5.0, fps, start=half[-1].tolist(), direction=(-1, 0))
        positions = np.vstack([half, back])
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.distance_covered_m > 10.0  # must be more than straight-line displacement


# ---------------------------------------------------------------------------
# compute_physical_metrics — speed
# ---------------------------------------------------------------------------

class TestSpeedMetrics:

    def test_top_speed_equals_constant_speed(self):
        fps = 25.0
        speed = 7.5
        positions = straight_line_positions(100, speed, fps)
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.top_speed_ms == pytest.approx(speed, rel=0.05)

    def test_avg_speed_of_constant_motion(self):
        fps = 25.0
        speed = 4.0
        positions = straight_line_positions(100, speed, fps)
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.avg_speed_ms == pytest.approx(speed, rel=0.05)

    def test_top_speed_exceeds_avg_speed_for_variable_motion(self):
        """A player who sprints then jogs has top > avg."""
        fps = 25.0
        sprint = straight_line_positions(25, 9.0, fps)
        jog    = straight_line_positions(75, 3.0, fps, start=sprint[-1].tolist())
        positions = np.vstack([sprint, jog])
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.top_speed_ms > m.avg_speed_ms

    def test_stationary_player_has_zero_speeds(self):
        positions = np.zeros((50, 2))
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=25.0)
        assert m.top_speed_ms == pytest.approx(0.0, abs=0.01)
        assert m.avg_speed_ms == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# compute_physical_metrics — sprint / high-intensity bout counting
# ---------------------------------------------------------------------------

class TestBoutCounting:

    def test_single_sprint_counts_as_one(self):
        fps = 25.0
        # 1 second jogging, 2 seconds sprinting, 1 second jogging
        jog_before = straight_line_positions(25, 3.0, fps)
        sprint     = straight_line_positions(50, 8.0, fps, start=jog_before[-1].tolist())
        jog_after  = straight_line_positions(25, 3.0, fps, start=sprint[-1].tolist())
        positions  = np.vstack([jog_before, sprint, jog_after])
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.sprint_count == 1

    def test_two_separate_sprints_count_as_two(self):
        fps = 25.0
        sprint1   = straight_line_positions(25, 8.0, fps)
        rest      = straight_line_positions(25, 2.0, fps, start=sprint1[-1].tolist())
        sprint2   = straight_line_positions(25, 8.0, fps, start=rest[-1].tolist())
        positions = np.vstack([sprint1, rest, sprint2])
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.sprint_count == 2

    def test_hi_run_count_for_sub_sprint_effort(self):
        fps = 25.0
        # Speed between hi_run threshold (5.5) and sprint threshold (7.0)
        jog      = straight_line_positions(25, 2.0, fps)
        hi_run   = straight_line_positions(25, 6.0, fps, start=jog[-1].tolist())
        positions = np.vstack([jog, hi_run])
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.hi_run_count >= 1
        assert m.sprint_count == 0   # 6 m/s is below sprint threshold (7.0)

    def test_no_sprints_for_slow_player(self):
        fps = 25.0
        positions = straight_line_positions(100, 3.0, fps)
        m = compute_physical_metrics(track_id=1, pitch_positions=positions, fps=fps)
        assert m.sprint_count == 0
        assert m.hi_run_count == 0

    def test_single_position_returns_zero_metrics(self):
        positions = np.array([[10.0, 20.0]])
        m = compute_physical_metrics(track_id=5, pitch_positions=positions, fps=25.0)
        assert m.distance_covered_m == 0.0
        assert m.top_speed_ms == 0.0
        assert m.sprint_count == 0
