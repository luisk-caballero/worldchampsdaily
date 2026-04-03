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


def test_batter_status_fuego() -> None:
    result = classify_batter_status(
        TrendRuleInput(
            WindowStats("T7D", {"ops": 0.930, "avg": 0.340}),
            WindowStats("YTD", {"ops": 0.810, "avg": 0.290}),
            WindowStats("Career", {"ops": 0.820, "avg": 0.300}),
        )
    )
    assert result == "Fuego"


def test_batter_status_steady_when_between_ytd_and_career() -> None:
    result = classify_batter_status(
        TrendRuleInput(
            WindowStats("T7D", {"ops": 0.890, "avg": 0.340}),
            WindowStats("YTD", {"ops": 0.850, "avg": 0.300}),
            WindowStats("Career", {"ops": 0.900, "avg": 0.330}),
        )
    )
    assert result == "Steady"


def test_pitcher_status_slump() -> None:
    result = classify_pitcher_status(
        TrendRuleInput(
            WindowStats("T7D", {"era": 6.80, "whip": 1.55}),
            WindowStats("YTD", {"era": 4.90, "whip": 1.32}),
            WindowStats("Baseline", {"era": 4.50, "whip": 1.28}),
        )
    )
    assert result == "Slump"


def test_pitcher_status_fuego() -> None:
    result = classify_pitcher_status(
        TrendRuleInput(
            WindowStats("T7D", {"era": 2.70, "whip": 1.02}),
            WindowStats("YTD", {"era": 3.80, "whip": 1.20}),
            WindowStats("Career", {"era": 3.60, "whip": 1.18}),
        )
    )
    assert result == "Fuego"
