from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from venezuelan_mlb_report.mlb_api import fetch_season_stats, search_person_by_name
from venezuelan_mlb_report.universe import TrackingRules, UniversePlayer


@dataclass
class LivePlayerSnapshot:
    seed_name: str
    mlb_name: str | None
    mlb_id: int | None
    role: str
    subrole: str | None
    tracking_tier: str
    must_track: bool
    groups: list[str]
    team_seed: str | None
    team_api: str | None
    birth_country: str | None
    active: bool | None
    selected_for_daily_report: bool
    selection_reason: str
    season: int
    stats: dict


@dataclass
class HistoricalSeasonSnapshot:
    seed_name: str
    mlb_name: str | None
    mlb_id: int | None
    role: str
    subrole: str | None
    tracking_tier: str
    must_track: bool
    groups: list[str]
    season: int
    team_api: str | None
    stats: dict


def _batter_selected(stats: dict, player: UniversePlayer, rules: TrackingRules) -> tuple[bool, str]:
    if player.tracking_tier == "core":
        return True, "core_tier"
    if any(group in rules.always_include_groups for group in player.groups):
        return True, "protected_group"
    plate_appearances = int(stats.get("plateAppearances", 0) or 0)
    if plate_appearances >= rules.batter_min_pa:
        return True, f"plate_appearances>={rules.batter_min_pa}"
    return False, "below_batter_threshold"


def _pitcher_selected(stats: dict, player: UniversePlayer, rules: TrackingRules) -> tuple[bool, str]:
    if player.tracking_tier == "core":
        return True, "core_tier"
    if any(group in rules.always_include_groups for group in player.groups):
        return True, "protected_group"
    innings = float(stats.get("inningsPitched", 0) or 0)
    appearances = int(stats.get("gamesPlayed", 0) or stats.get("gamesPitched", 0) or 0)
    if player.subrole == "reliever" and appearances >= rules.reliever_min_appearances:
        return True, f"appearances>={rules.reliever_min_appearances}"
    if innings >= rules.pitcher_min_ip:
        return True, f"innings_pitched>={rules.pitcher_min_ip}"
    return False, "below_pitcher_threshold"


def build_live_snapshots(
    players: list[UniversePlayer],
    rules: TrackingRules,
    season: int,
) -> list[LivePlayerSnapshot]:
    snapshots: list[LivePlayerSnapshot] = []
    for player in players:
        resolved = search_person_by_name(player.name)
        if resolved is None:
            snapshots.append(
                LivePlayerSnapshot(
                    seed_name=player.name,
                    mlb_name=None,
                    mlb_id=None,
                    role=player.role,
                    subrole=player.subrole,
                    tracking_tier=player.tracking_tier,
                    must_track=player.must_track,
                    groups=player.groups,
                    team_seed=player.team,
                    team_api=None,
                    birth_country=None,
                    active=None,
                    selected_for_daily_report=False,
                    selection_reason="player_not_found",
                    season=season,
                    stats={},
                )
            )
            continue

        season_payload = fetch_season_stats(resolved.mlb_id, player.role, season)
        stats = season_payload.get("stat", {})
        if player.role == "batter":
            selected, reason = _batter_selected(stats, player, rules)
        else:
            selected, reason = _pitcher_selected(stats, player, rules)
        snapshots.append(
            LivePlayerSnapshot(
                seed_name=player.name,
                mlb_name=resolved.full_name,
                mlb_id=resolved.mlb_id,
                role=player.role,
                subrole=player.subrole,
                tracking_tier=player.tracking_tier,
                must_track=player.must_track,
                groups=player.groups,
                team_seed=player.team,
                team_api=season_payload.get("team"),
                birth_country=resolved.birth_country,
                active=resolved.active,
                selected_for_daily_report=selected,
                selection_reason=reason,
                season=season,
                stats=stats,
            )
        )
    return snapshots


def write_snapshots(path: Path, snapshots: list[LivePlayerSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(snapshot) for snapshot in snapshots], indent=2), encoding="utf-8")


def build_historical_snapshots(
    players: list[UniversePlayer],
    season_start: int,
    season_end: int,
) -> list[HistoricalSeasonSnapshot]:
    snapshots: list[HistoricalSeasonSnapshot] = []
    for player in players:
        resolved = search_person_by_name(player.name)
        if resolved is None:
            continue
        for season in range(season_start, season_end + 1):
            season_payload = fetch_season_stats(resolved.mlb_id, player.role, season)
            stats = season_payload.get("stat", {})
            if not stats:
                continue
            snapshots.append(
                HistoricalSeasonSnapshot(
                    seed_name=player.name,
                    mlb_name=resolved.full_name,
                    mlb_id=resolved.mlb_id,
                    role=player.role,
                    subrole=player.subrole,
                    tracking_tier=player.tracking_tier,
                    must_track=player.must_track,
                    groups=player.groups,
                    season=season,
                    team_api=season_payload.get("team"),
                    stats=stats,
                )
            )
    return snapshots


def write_historical_snapshots(path: Path, snapshots: list[HistoricalSeasonSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(snapshot) for snapshot in snapshots], indent=2), encoding="utf-8")
