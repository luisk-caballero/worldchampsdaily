from __future__ import annotations

from dataclasses import dataclass

from venezuelan_mlb_report.models import WindowStats


@dataclass(frozen=True)
class TrendRuleInput:
    trailing_7: WindowStats
    ytd: WindowStats
    baseline: WindowStats


STEADY_BAND = 0.10


def _relative_delta(current: float, reference: float, *, higher_is_better: bool) -> float:
    baseline = max(abs(reference), 1e-6)
    raw = (current - reference) / baseline
    return raw if higher_is_better else -raw


def classify_batter_status(data: TrendRuleInput) -> str:
    t7_ops = data.trailing_7.metrics.get("ops", 0.0)
    ytd_ops = data.ytd.metrics.get("ops", 0.0)
    career_ops = data.baseline.metrics.get("ops", 0.0)
    t7_avg = data.trailing_7.metrics.get("avg", 0.0)
    ytd_avg = data.ytd.metrics.get("avg", 0.0)
    career_avg = data.baseline.metrics.get("avg", 0.0)

    pace_deltas = [
        _relative_delta(t7_ops, ytd_ops, higher_is_better=True),
        _relative_delta(t7_avg, ytd_avg, higher_is_better=True),
    ]
    quality_deltas = [
        _relative_delta(t7_ops, career_ops, higher_is_better=True),
        _relative_delta(t7_avg, career_avg, higher_is_better=True),
    ]

    pace_pos = any(delta >= STEADY_BAND for delta in pace_deltas)
    pace_neg = any(delta <= -STEADY_BAND for delta in pace_deltas)
    quality_pos = any(delta >= STEADY_BAND for delta in quality_deltas)
    quality_neg = any(delta <= -STEADY_BAND for delta in quality_deltas)

    if pace_pos and quality_pos:
        return "Fuego"
    if pace_neg and quality_neg:
        return "Slump"
    if all(abs(delta) <= STEADY_BAND for delta in pace_deltas + quality_deltas):
        return "Steady"
    if pace_pos or quality_pos:
        return "Hot"
    if pace_neg or quality_neg:
        return "Cooling off"
    return "Steady"


def classify_pitcher_status(data: TrendRuleInput) -> str:
    t7_era = data.trailing_7.metrics.get("era", 99.0)
    ytd_era = data.ytd.metrics.get("era", 99.0)
    career_era = data.baseline.metrics.get("era", 99.0)
    t7_whip = data.trailing_7.metrics.get("whip", 99.0)
    ytd_whip = data.ytd.metrics.get("whip", 99.0)
    career_whip = data.baseline.metrics.get("whip", 99.0)

    pace_deltas = [
        _relative_delta(t7_era, ytd_era, higher_is_better=False),
        _relative_delta(t7_whip, ytd_whip, higher_is_better=False),
    ]
    quality_deltas = [
        _relative_delta(t7_era, career_era, higher_is_better=False),
        _relative_delta(t7_whip, career_whip, higher_is_better=False),
    ]

    pace_pos = any(delta >= STEADY_BAND for delta in pace_deltas)
    pace_neg = any(delta <= -STEADY_BAND for delta in pace_deltas)
    quality_pos = any(delta >= STEADY_BAND for delta in quality_deltas)
    quality_neg = any(delta <= -STEADY_BAND for delta in quality_deltas)

    if pace_pos and quality_pos:
        return "Fuego"
    if pace_neg and quality_neg:
        return "Slump"
    if all(abs(delta) <= STEADY_BAND for delta in pace_deltas + quality_deltas):
        return "Steady"
    if pace_pos or quality_pos:
        return "Hot"
    if pace_neg or quality_neg:
        return "Cooling off"
    return "Steady"
