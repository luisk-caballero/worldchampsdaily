from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_UNIVERSE_PATH = Path("data/player_universe_seed_v1.json")
DEFAULT_TRACKING_RULES_PATH = Path("config/tracking_rules.json")


@dataclass
class UniversePlayer:
    name: str
    team: str | None
    role: str
    subrole: str | None
    groups: list[str]
    tracking_tier: str
    must_track: bool


@dataclass
class TrackingRules:
    batter_min_pa: int
    pitcher_min_ip: float
    reliever_min_appearances: int
    always_include_groups: list[str]


def load_universe(path: Path = DEFAULT_UNIVERSE_PATH) -> list[UniversePlayer]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        UniversePlayer(
            name=item["name"],
            team=item.get("team"),
            role=item["role"],
            subrole=item.get("subrole"),
            groups=item.get("groups", []),
            tracking_tier=item["tracking_tier"],
            must_track=bool(item.get("must_track", False)),
        )
        for item in raw
    ]


def load_tracking_rules(path: Path = DEFAULT_TRACKING_RULES_PATH) -> TrackingRules:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TrackingRules(
        batter_min_pa=int(raw["batters"]["default_min_plate_appearances_ytd"]),
        pitcher_min_ip=float(raw["pitchers"]["default_min_innings_pitched_ytd"]),
        reliever_min_appearances=int(raw["pitchers"]["default_min_appearances_ytd_for_relievers"]),
        always_include_groups=list(raw["batters"]["always_include_groups"]),
    )


def select_seed_players(
    players: list[UniversePlayer],
    tiers: tuple[str, ...] = ("core", "active"),
) -> list[UniversePlayer]:
    allowed = set(tiers)
    return [player for player in players if player.tracking_tier in allowed]
