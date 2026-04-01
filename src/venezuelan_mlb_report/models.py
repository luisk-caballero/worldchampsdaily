from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Player:
    mlb_id: int
    name: str
    role: str
    team: str
    team_logo_url: str | None = None
    subrole: str | None = None
    projection_games_target: int | None = None
    active: bool = True


@dataclass
class WindowStats:
    label: str
    metrics: dict[str, float]


@dataclass
class LastNightLine:
    opponent: str
    summary: str
    commentary: str
    source_url: str | None = None


@dataclass
class PlayerSnapshot:
    player: Player
    last_night: LastNightLine | None
    trailing_7: WindowStats
    ytd: WindowStats
    baseline: WindowStats
    status: str


@dataclass
class DailyReport:
    report_date: date
    refreshed_at: datetime | None = None
    batters: list[PlayerSnapshot] = field(default_factory=list)
    pitchers: list[PlayerSnapshot] = field(default_factory=list)
