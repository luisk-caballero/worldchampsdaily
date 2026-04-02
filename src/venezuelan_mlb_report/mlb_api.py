from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


BASE_URL = "https://statsapi.mlb.com/api/v1"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_RETRIES = 3
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


class MLBApiError(RuntimeError):
    pass


@dataclass
class ResolvedPlayer:
    mlb_id: int
    full_name: str
    birth_country: str | None
    active: bool
    current_team: str | None
    primary_position: str | None
    debut_date: str | None


def _read_url(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS, retries: int = DEFAULT_RETRIES) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(url, timeout=timeout) as response:
                return response.read()
        except HTTPError as exc:
            last_error = exc
            if exc.code not in RETRYABLE_HTTP_STATUSES or attempt == retries:
                break
        except URLError as exc:
            last_error = exc
            if attempt == retries:
                break
        time.sleep(1.5 * attempt)
    raise MLBApiError(f"Failed to fetch {url}: {last_error}") from last_error


def _get_json(url: str) -> dict[str, Any]:
    return json.loads(_read_url(url).decode("utf-8"))


def search_person_by_name(name: str) -> ResolvedPlayer | None:
    url = f"{BASE_URL}/people/search?names={quote(name)}"
    payload = _get_json(url)
    people = payload.get("people", [])
    if not people:
        return None
    person = people[0]
    return ResolvedPlayer(
        mlb_id=int(person["id"]),
        full_name=person["fullName"],
        birth_country=person.get("birthCountry"),
        active=bool(person.get("active", False)),
        current_team=None,
        primary_position=(person.get("primaryPosition") or {}).get("abbreviation"),
        debut_date=person.get("mlbDebutDate"),
    )


def fetch_season_stats(mlb_id: int, role: str, season: int) -> dict[str, Any]:
    group = "hitting" if role == "batter" else "pitching"
    url = f"{BASE_URL}/people/{mlb_id}/stats?stats=season&group={group}&season={season}"
    payload = _get_json(url)
    stats = payload.get("stats", [])
    if not stats:
        return {}
    splits = stats[0].get("splits", [])
    if not splits:
        return {}
    split = splits[0]
    return {
        "season": split.get("season"),
        "team": (split.get("team") or {}).get("name"),
        "league": (split.get("league") or {}).get("name"),
        "game_type": split.get("gameType"),
        "stat": split.get("stat", {}),
    }


def fetch_game_logs(mlb_id: int, role: str, season: int) -> list[dict[str, Any]]:
    group = "hitting" if role == "batter" else "pitching"
    url = f"{BASE_URL}/people/{mlb_id}/stats?stats=gameLog&group={group}&season={season}"
    payload = _get_json(url)
    stats = payload.get("stats", [])
    if not stats:
        return []
    return list(stats[0].get("splits", []))


def fetch_game_content(game_pk: int) -> dict[str, Any]:
    url = f"{BASE_URL}/game/{game_pk}/content"
    return _get_json(url)
