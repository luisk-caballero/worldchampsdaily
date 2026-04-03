from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

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

    pace_signal = mean(
        [
            _relative_delta(t7_ops, ytd_ops, higher_is_better=True),
            _relative_delta(t7_avg, ytd_avg, higher_is_better=True),
        ]
    )
    quality_signal = mean(
        [
            _relative_delta(t7_ops, career_ops, higher_is_better=True),
            _relative_delta(t7_avg, career_avg, higher_is_better=True),
        ]
    )

    if pace_signal >= STEADY_BAND and quality_signal >= STEADY_BAND:
        return "Fuego"
    if pace_signal <= -STEADY_BAND and quality_signal <= -STEADY_BAND:
        return "Slump"
    if abs(pace_signal) <= STEADY_BAND and abs(quality_signal) <= STEADY_BAND:
        return "Steady"
    if pace_signal >= STEADY_BAND or quality_signal >= STEADY_BAND:
        return "Hot"
    if pace_signal <= -STEADY_BAND or quality_signal <= -STEADY_BAND:
        return "Cooling off"
    return "Steady"


def classify_pitcher_status(data: TrendRuleInput) -> str:
    t7_era = data.trailing_7.metrics.get("era", 99.0)
    ytd_era = data.ytd.metrics.get("era", 99.0)
    career_era = data.baseline.metrics.get("era", 99.0)
    t7_whip = data.trailing_7.metrics.get("whip", 99.0)
    ytd_whip = data.ytd.metrics.get("whip", 99.0)
    career_whip = data.baseline.metrics.get("whip", 99.0)

    pace_signal = mean(
        [
            _relative_delta(t7_era, ytd_era, higher_is_better=False),
            _relative_delta(t7_whip, ytd_whip, higher_is_better=False),
        ]
    )
    quality_signal = mean(
        [
            _relative_delta(t7_era, career_era, higher_is_better=False),
            _relative_delta(t7_whip, career_whip, higher_is_better=False),
        ]
    )

    if pace_signal >= STEADY_BAND and quality_signal >= STEADY_BAND:
        return "Fuego"
    if pace_signal <= -STEADY_BAND and quality_signal <= -STEADY_BAND:
        return "Slump"
    if abs(pace_signal) <= STEADY_BAND and abs(quality_signal) <= STEADY_BAND:
        return "Steady"
    if pace_signal > STEADY_BAND or quality_signal > STEADY_BAND:
        return "Hot"
    if pace_signal < -STEADY_BAND or quality_signal < -STEADY_BAND:
        return "Cooling off"
    return "Steady"
