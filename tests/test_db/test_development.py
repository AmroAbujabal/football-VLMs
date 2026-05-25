"""
tests/test_metrics/test_development.py

TDD tests for metrics/development.py — DevelopmentScore computation.

Run with: pytest tests/test_metrics/test_development.py -v
"""

import pytest
from unittest.mock import MagicMock


def _stats(**overrides):
    """Build a mock PlayerMatchStats with sensible defaults."""
    s = MagicMock()
    s.distance_covered_m = overrides.get("distance_covered_m", 9000.0)
    s.sprint_count        = overrides.get("sprint_count",        15)
    s.hi_run_count        = overrides.get("hi_run_count",        25)
    s.top_speed_ms        = overrides.get("top_speed_ms",        7.0)
    s.pitch_control_contribution = overrides.get("pitch_control_contribution", 0.075)
    s.press_success_rate         = overrides.get("press_success_rate",         0.5)
    s.press_trigger_accuracy     = overrides.get("press_trigger_accuracy",     0.5)
    return s


class TestPhysicalScore:

    def test_perfect_physical_metrics_give_ten(self):
        from metrics.development import compute_development_score
        s = _stats(distance_covered_m=12000, sprint_count=30, hi_run_count=50, top_speed_ms=9.0)
        result = compute_development_score(s)
        assert result["physical_score"] == pytest.approx(10.0, abs=0.01)

    def test_zero_physical_metrics_give_zero(self):
        from metrics.development import compute_development_score
        s = _stats(distance_covered_m=5000, sprint_count=0, hi_run_count=0, top_speed_ms=5.0)
        result = compute_development_score(s)
        assert result["physical_score"] == pytest.approx(0.0, abs=0.01)

    def test_scores_are_clipped_at_zero(self):
        from metrics.development import compute_development_score
        s = _stats(distance_covered_m=0, sprint_count=-5, hi_run_count=-1, top_speed_ms=0)
        result = compute_development_score(s)
        assert result["physical_score"] >= 0.0

    def test_scores_are_clipped_at_ten(self):
        from metrics.development import compute_development_score
        s = _stats(distance_covered_m=99999, sprint_count=999, hi_run_count=999, top_speed_ms=99)
        result = compute_development_score(s)
        assert result["physical_score"] == pytest.approx(10.0, abs=0.01)

    def test_none_metrics_excluded_from_average(self):
        from metrics.development import compute_development_score
        # Only distance is available
        s = _stats(distance_covered_m=12000, sprint_count=None, hi_run_count=None, top_speed_ms=None)
        result = compute_development_score(s)
        assert result["physical_score"] == pytest.approx(10.0, abs=0.01)

    def test_all_none_physical_gives_none(self):
        from metrics.development import compute_development_score
        s = _stats(distance_covered_m=None, sprint_count=None, hi_run_count=None, top_speed_ms=None)
        result = compute_development_score(s)
        assert result["physical_score"] is None


class TestTacticalScore:

    def test_perfect_tactical_gives_ten(self):
        from metrics.development import compute_development_score
        s = _stats(pitch_control_contribution=0.15, press_success_rate=1.0)
        result = compute_development_score(s)
        assert result["tactical_score"] == pytest.approx(10.0, abs=0.01)

    def test_zero_tactical_gives_zero(self):
        from metrics.development import compute_development_score
        s = _stats(pitch_control_contribution=0.0, press_success_rate=0.0)
        result = compute_development_score(s)
        assert result["tactical_score"] == pytest.approx(0.0, abs=0.01)

    def test_none_tactical_metrics_give_none(self):
        from metrics.development import compute_development_score
        s = _stats(pitch_control_contribution=None, press_success_rate=None)
        result = compute_development_score(s)
        assert result["tactical_score"] is None


class TestTechnicalScore:

    def test_perfect_technical_gives_ten(self):
        from metrics.development import compute_development_score
        s = _stats(press_trigger_accuracy=1.0)
        result = compute_development_score(s)
        assert result["technical_score"] == pytest.approx(10.0, abs=0.01)

    def test_zero_technical_gives_zero(self):
        from metrics.development import compute_development_score
        s = _stats(press_trigger_accuracy=0.0)
        result = compute_development_score(s)
        assert result["technical_score"] == pytest.approx(0.0, abs=0.01)

    def test_none_technical_gives_none(self):
        from metrics.development import compute_development_score
        s = _stats(press_trigger_accuracy=None)
        result = compute_development_score(s)
        assert result["technical_score"] is None


class TestOverallScore:

    def test_overall_is_weighted_average_of_sub_scores(self):
        from metrics.development import compute_development_score
        # physical=10, tactical=10, technical=10 → overall=10
        s = _stats(
            distance_covered_m=12000, sprint_count=30, hi_run_count=50, top_speed_ms=9.0,
            pitch_control_contribution=0.15, press_success_rate=1.0,
            press_trigger_accuracy=1.0,
        )
        result = compute_development_score(s)
        assert result["overall_score"] == pytest.approx(10.0, abs=0.01)

    def test_overall_excludes_none_sub_scores_from_average(self):
        from metrics.development import compute_development_score
        # Only physical=10, rest None → overall should still be 10
        s = _stats(
            distance_covered_m=12000, sprint_count=30, hi_run_count=50, top_speed_ms=9.0,
            pitch_control_contribution=None, press_success_rate=None,
            press_trigger_accuracy=None,
        )
        result = compute_development_score(s)
        assert result["overall_score"] == pytest.approx(10.0, abs=0.01)

    def test_overall_is_between_zero_and_ten(self):
        from metrics.development import compute_development_score
        s = _stats()
        result = compute_development_score(s)
        assert 0.0 <= result["overall_score"] <= 10.0
