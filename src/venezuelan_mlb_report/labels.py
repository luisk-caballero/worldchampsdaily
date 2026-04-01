from __future__ import annotations

from dataclasses import dataclass

from venezuelan_mlb_report.models import WindowStats


@dataclass(frozen=True)
class TrendRuleInput:
    trailing_7: WindowStats
    ytd: WindowStats
    baseline: WindowStats


def classify_batter_status(data: TrendRuleInput) -> str:
    t7_ops = data.trailing_7.metrics.get("ops", 0.0)
    ytd_ops = data.ytd.metrics.get("ops", 0.0)
    base_ops = data.baseline.metrics.get("ops", 0.0)

    if t7_ops >= ytd_ops + 0.125 and t7_ops >= base_ops + 0.100:
        return "Hot"
    if t7_ops <= ytd_ops - 0.175 and t7_ops <= base_ops - 0.150:
        return "Slump"
    if t7_ops < ytd_ops - 0.050:
        return "Cooling off"
    return "Steady"


def classify_pitcher_status(data: TrendRuleInput) -> str:
    t7_era = data.trailing_7.metrics.get("era", 99.0)
    ytd_era = data.ytd.metrics.get("era", 99.0)
    base_era = data.baseline.metrics.get("era", 99.0)
    t7_whip = data.trailing_7.metrics.get("whip", 99.0)
    ytd_whip = data.ytd.metrics.get("whip", 99.0)

    if t7_era <= ytd_era - 0.75 and t7_era <= base_era - 0.50 and t7_whip <= ytd_whip - 0.10:
        return "Hot"
    if t7_era >= ytd_era + 1.25 and t7_era >= base_era + 1.00:
        return "Slump"
    if t7_era > ytd_era + 0.35 or t7_whip > ytd_whip + 0.08:
        return "Cooling off"
    return "Steady"
