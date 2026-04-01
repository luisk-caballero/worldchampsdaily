from __future__ import annotations

from datetime import date

from venezuelan_mlb_report.labels import (
    TrendRuleInput,
    classify_batter_status,
    classify_pitcher_status,
)
from venezuelan_mlb_report.models import DailyReport, LastNightLine, Player, PlayerSnapshot, WindowStats


def build_sample_report() -> DailyReport:
    batter_1 = _batter_snapshot(
        player=Player(
            660670,
            "Ronald Acuna Jr.",
            "batter",
            "ATL",
            team_logo_url="https://www.mlbstatic.com/team-logos/team-cap-on-light/144.svg",
            projection_games_target=162,
        ),
        opponent="PHI",
        summary="2-4, HR, 2 RBI, BB, SB",
        commentary="MLB.com: Acuna sparked Atlanta's offense early and stayed at the center of every scoring threat.",
        trailing_7={"games": 6, "avg": 0.333, "ops": 1.045, "hits": 8, "xbh": 4, "hr": 2},
        ytd={"games": 118, "avg": 0.289, "ops": 0.901, "hits": 141, "xbh": 57, "hr": 24},
        baseline={"games": 140, "avg": 0.292, "ops": 0.882, "hits": 154, "xbh": 59, "hr": 22},
    )
    batter_2 = _batter_snapshot(
        player=Player(
            543037,
            "Jose Altuve",
            "batter",
            "HOU",
            team_logo_url="https://www.mlbstatic.com/team-logos/team-cap-on-light/117.svg",
            projection_games_target=162,
        ),
        opponent="SEA",
        summary="0-4, 2 K",
        commentary="Houston Chronicle: Altuve's timing looked a touch late, and the Astros never found a rally behind him.",
        trailing_7={"games": 7, "avg": 0.179, "ops": 0.510, "hits": 5, "xbh": 1, "hr": 0},
        ytd={"games": 124, "avg": 0.271, "ops": 0.741, "hits": 132, "xbh": 36, "hr": 12},
        baseline={"games": 142, "avg": 0.306, "ops": 0.831, "hits": 173, "xbh": 50, "hr": 22},
    )
    pitcher_1 = _pitcher_snapshot(
        player=Player(
            622491,
            "Pablo Lopez",
            "pitcher",
            "MIN",
            team_logo_url="https://www.mlbstatic.com/team-logos/team-cap-on-light/142.svg",
            subrole="starter",
            projection_games_target=40,
        ),
        opponent="DET",
        summary="6.0 IP, 1 ER, 8 K, 1 BB",
        commentary="Star Tribune: Lopez leaned on the fastball-changeup mix and never let Detroit settle in.",
        trailing_7={"games": 1, "era": 2.10, "whip": 0.98, "k_per_9": 10.8, "strikeouts": 8, "wins": 1, "saves": 0},
        ytd={"games": 24, "era": 3.62, "whip": 1.19, "k_per_9": 9.5, "strikeouts": 156, "wins": 11, "saves": 0},
        baseline={"games": 30, "era": 3.84, "whip": 1.17, "k_per_9": 9.2, "strikeouts": 191, "wins": 14, "saves": 0},
    )
    pitcher_2 = _pitcher_snapshot(
        player=Player(
            606192,
            "Eduardo Rodriguez",
            "pitcher",
            "AZ",
            team_logo_url="https://www.mlbstatic.com/team-logos/team-cap-on-light/109.svg",
            subrole="starter",
            projection_games_target=40,
        ),
        opponent="LAD",
        summary="4.1 IP, 5 ER, 3 K, 3 BB",
        commentary="Arizona Republic: Rodriguez struggled to finish hitters once Los Angeles got traffic on the bases.",
        trailing_7={"games": 1, "era": 6.75, "whip": 1.61, "k_per_9": 7.4, "strikeouts": 3, "wins": 0, "saves": 0},
        ytd={"games": 22, "era": 4.82, "whip": 1.33, "k_per_9": 8.2, "strikeouts": 121, "wins": 8, "saves": 0},
        baseline={"games": 28, "era": 4.09, "whip": 1.29, "k_per_9": 8.5, "strikeouts": 168, "wins": 12, "saves": 0},
    )
    pitcher_3 = _pitcher_snapshot(
        player=Player(
            621052,
            "Jose Alvarado",
            "pitcher",
            "PHI",
            team_logo_url="https://www.mlbstatic.com/team-logos/team-cap-on-light/143.svg",
            subrole="reliever",
            projection_games_target=65,
        ),
        opponent="ATL",
        summary="1.0 IP, 0 ER, 2 K, SV",
        commentary="Philadelphia Inquirer: Alvarado's fastball had late life and closed the door quickly in the ninth.",
        trailing_7={"games": 3, "era": 0.00, "whip": 0.67, "k_per_9": 13.5, "strikeouts": 5, "wins": 0, "saves": 2},
        ytd={"games": 54, "era": 2.91, "whip": 1.08, "k_per_9": 11.7, "strikeouts": 70, "wins": 4, "saves": 24},
        baseline={"games": 61, "era": 3.26, "whip": 1.20, "k_per_9": 11.3, "strikeouts": 77, "wins": 4, "saves": 18},
    )
    return DailyReport(
        report_date=date.today(),
        batters=[batter_1, batter_2],
        pitchers=[pitcher_1, pitcher_2, pitcher_3],
    )


def _batter_snapshot(
    player: Player,
    opponent: str,
    summary: str,
    commentary: str,
    trailing_7: dict[str, float],
    ytd: dict[str, float],
    baseline: dict[str, float],
) -> PlayerSnapshot:
    trailing_window = WindowStats("Trailing 7 Days", trailing_7)
    ytd_window = WindowStats("Year to Date", ytd)
    baseline_window = WindowStats("Historical Baseline", baseline)
    status = classify_batter_status(TrendRuleInput(trailing_window, ytd_window, baseline_window))
    return PlayerSnapshot(
        player=player,
        last_night=LastNightLine(opponent, summary, commentary),
        trailing_7=trailing_window,
        ytd=ytd_window,
        baseline=baseline_window,
        status=status,
    )


def _pitcher_snapshot(
    player: Player,
    opponent: str,
    summary: str,
    commentary: str,
    trailing_7: dict[str, float],
    ytd: dict[str, float],
    baseline: dict[str, float],
) -> PlayerSnapshot:
    trailing_window = WindowStats("Trailing 7 Days", trailing_7)
    ytd_window = WindowStats("Year to Date", ytd)
    baseline_window = WindowStats("Historical Baseline", baseline)
    status = classify_pitcher_status(TrendRuleInput(trailing_window, ytd_window, baseline_window))
    return PlayerSnapshot(
        player=player,
        last_night=LastNightLine(opponent, summary, commentary),
        trailing_7=trailing_window,
        ytd=ytd_window,
        baseline=baseline_window,
        status=status,
    )
