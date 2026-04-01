from venezuelan_mlb_report.labels import (
    TrendRuleInput,
    classify_batter_status,
    classify_pitcher_status,
)
from venezuelan_mlb_report.models import WindowStats


def test_batter_status_hot() -> None:
    result = classify_batter_status(
        TrendRuleInput(
            WindowStats("T7D", {"ops": 1.020}),
            WindowStats("YTD", {"ops": 0.830}),
            WindowStats("Baseline", {"ops": 0.860}),
        )
    )
    assert result == "Hot"


def test_pitcher_status_slump() -> None:
    result = classify_pitcher_status(
        TrendRuleInput(
            WindowStats("T7D", {"era": 6.80, "whip": 1.55}),
            WindowStats("YTD", {"era": 4.90, "whip": 1.32}),
            WindowStats("Baseline", {"era": 4.50, "whip": 1.28}),
        )
    )
    assert result == "Slump"
