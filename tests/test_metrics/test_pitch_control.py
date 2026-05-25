"""
tests/test_metrics/test_pitch_control.py
"""

import numpy as np
import pytest

from metrics.pitch_control import (
    compute_pitch_control,
    player_influence,
    GRID_POINTS,
)
from tracking.types import Track


def make_track(track_id: int, pitch_pos: tuple, team: str = "home") -> Track:
    track = Track(
        track_id=track_id,
        bbox=np.array([0.0, 0.0, 50.0, 150.0]),
        team=team,
    )
    track.pitch_pos = np.array(pitch_pos, dtype=float)
    return track


class TestPlayerInfluence:

    def test_influence_peaks_at_player_position(self):
        pos = np.array([52.5, 34.0])  # centre of pitch
        inf = player_influence(pos, None)
        # Find the grid cell closest to the player
        dists = np.linalg.norm(GRID_POINTS - pos, axis=1)
        closest_cell = np.argmin(dists)
        assert inf[closest_cell] == pytest.approx(inf.max(), rel=0.05)

    def test_influence_sums_positive(self):
        pos = np.array([20.0, 15.0])
        inf = player_influence(pos, None)
        assert inf.sum() > 0
        assert (inf >= 0).all()


class TestPitchControl:

    def test_symmetric_teams_equal_control(self):
        """Two teams with mirrored positions should share control ~50/50."""
        home = [
            make_track(1, (20.0, 15.0), "home"),
            make_track(2, (50.0, 34.0), "home"),
            make_track(3, (80.0, 50.0), "home"),
        ]
        away = [
            make_track(4, (85.0, 53.0), "away"),
            make_track(5, (55.0, 34.0), "away"),
            make_track(6, (25.0, 19.0), "away"),
        ]
        result = compute_pitch_control(frame_id=0, home_tracks=home, away_tracks=away)
        assert 0.3 < result.home_control_pct < 0.7

    def test_home_dominates_when_forward(self):
        """Home team clustered near opposition goal should dominate control."""
        home = [make_track(i, (90.0, 34.0), "home") for i in range(5)]
        away = [make_track(i + 10, (10.0, 34.0), "away") for i in range(5)]
        result = compute_pitch_control(0, home, away)
        # Home should control more of the pitch overall
        assert result.home_control_pct > 0.5

    def test_player_contributions_present(self):
        home = [make_track(1, (52.5, 34.0), "home")]
        away = [make_track(2, (52.5, 34.0), "away")]
        result = compute_pitch_control(0, home, away)
        assert 1 in result.player_contributions
        assert 2 in result.player_contributions

    def test_surfaces_sum_to_one(self):
        home = [make_track(1, (30.0, 20.0), "home")]
        away = [make_track(2, (70.0, 48.0), "away")]
        result = compute_pitch_control(0, home, away)
        surface_sum = result.home_surface + result.away_surface
        np.testing.assert_allclose(surface_sum, np.ones_like(surface_sum), atol=1e-6)
