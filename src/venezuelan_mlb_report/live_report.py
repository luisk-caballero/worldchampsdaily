from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from venezuelan_mlb_report.labels import TrendRuleInput, classify_batter_status, classify_pitcher_status
from venezuelan_mlb_report.mlb_api import MLBApiError, _read_url, fetch_game_content, fetch_game_logs
from venezuelan_mlb_report.models import DailyReport, LastNightLine, Player, PlayerSnapshot, WindowStats
from venezuelan_mlb_report.report import render_email_report_html

TEAM_LOGO_IDS = {
    "LAA": 108,
    "ANA": 108,
    "ARI": 109,
    "AZ": 109,
    "ATL": 144,
    "BAL": 110,
    "BOS": 111,
    "CHC": 112,
    "CIN": 113,
    "CLE": 114,
    "COL": 115,
    "CWS": 145,
    "CHW": 145,
    "DET": 116,
    "HOU": 117,
    "KC": 118,
    "KCR": 118,
    "LAD": 119,
    "WSH": 120,
    "WAS": 120,
    "NYY": 147,
    "ATH": 133,
    "OAK": 133,
    "PIT": 134,
    "SD": 135,
    "SDP": 135,
    "STL": 138,
    "TEX": 140,
    "TBR": 139,
    "PHI": 143,
    "MIA": 146,
    "MIL": 158,
    "MIN": 142,
    "NYM": 121,
    "SEA": 136,
    "SFG": 137,
    "SF": 137,
    "TB": 139,
    "TOR": 141,
}
NOTE_SOURCES_PATH = Path("config/note_sources.json")
TEAM_NAME_TO_ABBREV = {
    "Arizona Diamondbacks": "AZ",
    "Athletics": "ATH",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}
TEAM_ABBREV_TO_NAME = {
    "ATH": "Athletics",
    "ATL": "Atlanta Braves",
    "AZ": "Arizona Diamondbacks",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "CWS": "Chicago White Sox",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KC": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "SEA": "Seattle Mariners",
    "SF": "San Francisco Giants",
    "STL": "St. Louis Cardinals",
    "TB": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WSH": "Washington Nationals"
}


def _team_logo_url(team_abbrev: str | None) -> str | None:
    if not team_abbrev:
        return None
    team_id = TEAM_LOGO_IDS.get(team_abbrev)
    if team_id is None:
        return None
    return f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{team_id}.svg"


def _team_abbrev_from_name(team_name: str | None) -> str:
    if not team_name:
        return ""
    return TEAM_NAME_TO_ABBREV.get(team_name, team_name)


def _load_allowed_sources() -> list[str]:
    raw = json.loads(NOTE_SOURCES_PATH.read_text(encoding="utf-8"))
    return list(raw.get("allowed_sources", []))


def _build_mlb_note(game_pk: int, player_name: str, cache: dict[int, tuple[str, str | None]]) -> tuple[str, str | None]:
    if game_pk in cache:
        return cache[game_pk]
    content = fetch_game_content(game_pk)
    recap = ((content.get("editorial") or {}).get("recap") or {}).get("mlb") or {}
    headline = recap.get("headline", "").strip()
    blurb = recap.get("blurb", "").strip()
    slug = recap.get("slug", "").strip()
    player_last_name = player_name.split()[-1].replace(".", "").lower()
    note = ""
    link = f"https://www.mlb.com/news/{slug}" if slug else None
    combined = f"{headline} {blurb}".lower()
    if player_last_name and player_last_name in combined:
        note = f"MLB.com: {headline or blurb}"
    cache[game_pk] = (note, link if note else None)
    return cache[game_pk]


def _strip_html(text: str) -> str:
    parts: list[str] = []
    inside = False
    for char in text:
        if char == "<":
            inside = True
            continue
        if char == ">":
            inside = False
            continue
        if not inside:
            parts.append(char)
    return "".join(parts).replace("\xa0", " ").strip()


def _extract_source(description: str) -> str:
    if "<font" not in description:
        return ""
    return description.split("<font", 1)[-1].split(">", 1)[-1].split("<", 1)[0].strip()


def _search_external_note(
    player_name: str,
    opponent: str,
    team: str,
    game_date: date,
    allowed_sources: list[str],
    cache: dict[tuple[str, str], tuple[str, str | None]],
) -> tuple[str, str | None]:
    key = (player_name, opponent)
    if key in cache:
        return cache[key]
    external_sources = [source for source in allowed_sources if source != "mlb.com"]
    if not external_sources:
        cache[key] = ("", None)
        return cache[key]
    sources_query = " OR ".join(f"site:{source}" for source in external_sources)
    query = f'"{player_name}" "{opponent}" "{team}" ({sources_query}) ("game recap" OR recap OR beat OR defeated OR win OR loss)'
    url = "https://news.google.com/rss/search?q=" + quote(query)
    try:
        root = ET.fromstring(_read_url(url))
    except Exception:
        cache[key] = ("", None)
        return cache[key]
    player_last_name = player_name.split()[-1].replace(".", "").lower()
    team_name = TEAM_ABBREV_TO_NAME.get(team, team)
    best_match: tuple[str, str | None] = ("", None)
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        description_raw = item.findtext("description") or ""
        description = _strip_html(description_raw)
        source = _extract_source(description_raw)
        pub_date = _parse_pub_date(item.findtext("pubDate") or "")
        if pub_date is not None and abs((pub_date.date() - game_date).days) > 1:
            continue
        combined = f"{title} {description}".lower()
        recapish = any(token in combined for token in ("recap", "beat", "defeat", "defeated", "win", "loss", "box score", "highlights"))
        opponentish = opponent.lower() in combined if opponent else False
        teamish = team.lower() in combined or team_name.lower() in combined
        if player_last_name and player_last_name in combined and recapish and opponentish and teamish:
            note = f"{source or 'Recap'}: {title}"
            link = item.findtext("link")
            if pub_date is not None and pub_date.date() == game_date:
                cache[key] = (note, link)
                return cache[key]
            if not best_match[0]:
                best_match = (note, link)
    cache[key] = best_match
    return cache[key]


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_pub_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _safe_int(value: object) -> int:
    if value in (None, "", "-.--", ".---"):
        return 0
    return int(float(value))


def _safe_float(value: object) -> float:
    if value in (None, "", "-.--", ".---"):
        return 0.0
    return float(value)


def _safe_avg(value: object) -> float:
    if value in (None, "", "-.--", ".---"):
        return 0.0
    return float(str(value).lstrip(".") and value if str(value).startswith("0") else f"0{value}" if str(value).startswith(".") else value)


def _sum_batter_window(logs: list[dict], start_date: date, end_date: date) -> dict[str, float]:
    filtered = [log for log in logs if start_date <= _parse_date(log["date"]) <= end_date]
    at_bats = sum(_safe_int(log["stat"].get("atBats")) for log in filtered)
    hits = sum(_safe_int(log["stat"].get("hits")) for log in filtered)
    walks = sum(_safe_int(log["stat"].get("baseOnBalls")) for log in filtered)
    hbp = sum(_safe_int(log["stat"].get("hitByPitch")) for log in filtered)
    sac_flies = sum(_safe_int(log["stat"].get("sacFlies")) for log in filtered)
    total_bases = sum(_safe_int(log["stat"].get("totalBases")) for log in filtered)
    doubles = sum(_safe_int(log["stat"].get("doubles")) for log in filtered)
    triples = sum(_safe_int(log["stat"].get("triples")) for log in filtered)
    home_runs = sum(_safe_int(log["stat"].get("homeRuns")) for log in filtered)
    plate_appearances = sum(_safe_int(log["stat"].get("plateAppearances")) for log in filtered)
    avg = hits / at_bats if at_bats else 0.0
    obp_denom = at_bats + walks + hbp + sac_flies
    obp = (hits + walks + hbp) / obp_denom if obp_denom else 0.0
    slg = total_bases / at_bats if at_bats else 0.0
    return {
        "games": len(filtered),
        "avg": avg,
        "ops": obp + slg,
        "hits": hits,
        "xbh": doubles + triples + home_runs,
        "hr": home_runs,
        "plate_appearances": plate_appearances,
    }


def _sum_pitcher_window(logs: list[dict], start_date: date, end_date: date) -> dict[str, float]:
    filtered = [log for log in logs if start_date <= _parse_date(log["date"]) <= end_date]
    innings = sum(_safe_float(log["stat"].get("inningsPitched")) for log in filtered)
    earned_runs = sum(_safe_int(log["stat"].get("earnedRuns")) for log in filtered)
    walks = sum(_safe_int(log["stat"].get("baseOnBalls")) for log in filtered)
    hits = sum(_safe_int(log["stat"].get("hits")) for log in filtered)
    strikeouts = sum(_safe_int(log["stat"].get("strikeOuts")) for log in filtered)
    wins = sum(1 for log in filtered if _safe_int(log["stat"].get("wins")) > 0)
    saves = sum(1 for log in filtered if _safe_int(log["stat"].get("saves")) > 0)
    era = (earned_runs * 9 / innings) if innings else 0.0
    whip = ((walks + hits) / innings) if innings else 0.0
    k_per_9 = (strikeouts * 9 / innings) if innings else 0.0
    return {
        "games": len(filtered),
        "era": era,
        "whip": whip,
        "k_per_9": k_per_9,
        "strikeouts": strikeouts,
        "wins": wins,
        "saves": saves,
        "innings": innings,
    }


def _batter_ytd_metrics(stats: dict) -> dict[str, float]:
    return {
        "games": _safe_int(stats.get("gamesPlayed")),
        "avg": _safe_avg(stats.get("avg")),
        "ops": _safe_avg(stats.get("ops")),
        "hits": _safe_int(stats.get("hits")),
        "xbh": _safe_int(stats.get("doubles")) + _safe_int(stats.get("triples")) + _safe_int(stats.get("homeRuns")),
        "hr": _safe_int(stats.get("homeRuns")),
        "plate_appearances": _safe_int(stats.get("plateAppearances")),
    }


def _pitcher_ytd_metrics(stats: dict) -> dict[str, float]:
    return {
        "games": _safe_int(stats.get("gamesPlayed") or stats.get("gamesPitched")),
        "era": _safe_avg(stats.get("era")),
        "whip": _safe_avg(stats.get("whip")),
        "k_per_9": _safe_avg(stats.get("strikeoutsPer9Inn") or stats.get("strikeoutsPer9") or stats.get("kPer9") or stats.get("k_per_9")),
        "strikeouts": _safe_int(stats.get("strikeOuts")),
        "wins": _safe_int(stats.get("wins")),
        "saves": _safe_int(stats.get("saves")),
        "innings": _safe_float(stats.get("inningsPitched")),
    }


def _aggregate_batter_history(rows: list[dict]) -> dict[str, float]:
    games = sum(_safe_int(row["stats"].get("gamesPlayed")) for row in rows)
    at_bats = sum(_safe_int(row["stats"].get("atBats")) for row in rows)
    hits = sum(_safe_int(row["stats"].get("hits")) for row in rows)
    walks = sum(_safe_int(row["stats"].get("baseOnBalls")) for row in rows)
    hbp = sum(_safe_int(row["stats"].get("hitByPitch")) for row in rows)
    sac_flies = sum(_safe_int(row["stats"].get("sacFlies")) for row in rows)
    total_bases = sum(_safe_int(row["stats"].get("totalBases")) for row in rows)
    doubles = sum(_safe_int(row["stats"].get("doubles")) for row in rows)
    triples = sum(_safe_int(row["stats"].get("triples")) for row in rows)
    home_runs = sum(_safe_int(row["stats"].get("homeRuns")) for row in rows)
    avg = hits / at_bats if at_bats else 0.0
    obp_denom = at_bats + walks + hbp + sac_flies
    obp = (hits + walks + hbp) / obp_denom if obp_denom else 0.0
    slg = total_bases / at_bats if at_bats else 0.0
    return {
        "games": games,
        "avg": avg,
        "ops": obp + slg,
        "hits": hits,
        "xbh": doubles + triples + home_runs,
        "hr": home_runs,
    }


def _aggregate_pitcher_history(rows: list[dict]) -> dict[str, float]:
    games = sum(_safe_int(row["stats"].get("gamesPlayed") or row["stats"].get("gamesPitched")) for row in rows)
    innings = sum(_safe_float(row["stats"].get("inningsPitched")) for row in rows)
    earned_runs = sum(_safe_int(row["stats"].get("earnedRuns")) for row in rows)
    walks = sum(_safe_int(row["stats"].get("baseOnBalls")) for row in rows)
    hits = sum(_safe_int(row["stats"].get("hits")) for row in rows)
    strikeouts = sum(_safe_int(row["stats"].get("strikeOuts")) for row in rows)
    wins = sum(_safe_int(row["stats"].get("wins")) for row in rows)
    saves = sum(_safe_int(row["stats"].get("saves")) for row in rows)
    era = earned_runs * 9 / innings if innings else 0.0
    whip = (walks + hits) / innings if innings else 0.0
    k_per_9 = strikeouts * 9 / innings if innings else 0.0
    return {
        "games": games,
        "era": era,
        "whip": whip,
        "k_per_9": k_per_9,
        "strikeouts": strikeouts,
        "wins": wins,
        "saves": saves,
    }


def build_live_daily_report(
    live_path: Path,
    historical_path: Path,
    as_of_date: date,
    season: int,
) -> DailyReport:
    live_rows = json.loads(live_path.read_text(encoding="utf-8"))
    historical_rows = json.loads(historical_path.read_text(encoding="utf-8"))
    prior_date = as_of_date - timedelta(days=1)
    trailing_start = prior_date - timedelta(days=6)
    snapshots: list[PlayerSnapshot] = []
    note_cache: dict[int, tuple[str, str | None]] = {}
    external_note_cache: dict[tuple[str, str], tuple[str, str | None]] = {}
    allowed_sources = _load_allowed_sources()
    for row in live_rows:
        if not row["selected_for_daily_report"] or row["mlb_id"] is None:
            continue
        try:
            logs = fetch_game_logs(row["mlb_id"], row["role"], season)
        except MLBApiError as exc:
            # Keep report generation resilient when individual player log fetches fail.
            print(f"Warning: skipping game logs for {row['seed_name']} ({row['mlb_id']}): {exc}")
            logs = []
        prior_logs = [log for log in logs if _parse_date(log["date"]) == prior_date]
        last_night = None
        if prior_logs:
            latest_log = prior_logs[-1]
            game_pk = ((latest_log.get("game") or {}).get("gamePk")) or 0
            note_text = ""
            note_url = None
            if game_pk:
                try:
                    note_text, note_url = _build_mlb_note(game_pk, row["seed_name"], note_cache)
                except MLBApiError as exc:
                    print(f"Warning: note lookup failed for game {game_pk} ({row['seed_name']}): {exc}")
                    note_text, note_url = "", None
            if not note_text:
                note_text, note_url = _search_external_note(
                    row["seed_name"],
                    (latest_log.get("opponent") or {}).get("name", ""),
                    row.get("team_seed") or "",
                    prior_date,
                    allowed_sources,
                    external_note_cache,
                )
            last_night = LastNightLine(
                opponent=_team_abbrev_from_name((latest_log.get("opponent") or {}).get("name", "")),
                summary=latest_log["stat"].get("summary", ""),
                commentary=note_text,
                source_url=note_url,
            )
        history_rows = [h for h in historical_rows if h["seed_name"] == row["seed_name"]]
        player = Player(
            mlb_id=row["mlb_id"],
            name=row["seed_name"],
            role=row["role"],
            team=row.get("team_seed") or "",
            team_logo_url=_team_logo_url(row.get("team_seed")),
            subrole=row.get("subrole"),
            projection_games_target=162 if row["role"] == "batter" else (65 if row.get("subrole") == "reliever" else 40),
            active=bool(row.get("active", True)),
        )
        if row["role"] == "batter":
            trailing_metrics = _sum_batter_window(logs, trailing_start, prior_date)
            ytd_metrics = _batter_ytd_metrics(row["stats"])
            career_metrics = _aggregate_batter_history(history_rows)
            status = classify_batter_status(
                TrendRuleInput(
                    WindowStats("Trailing 7 Days", trailing_metrics),
                    WindowStats("Year to Date", ytd_metrics),
                    WindowStats("Career", career_metrics),
                )
            )
        else:
            trailing_metrics = _sum_pitcher_window(logs, trailing_start, prior_date)
            ytd_metrics = _pitcher_ytd_metrics(row["stats"])
            career_metrics = _aggregate_pitcher_history(history_rows)
            status = classify_pitcher_status(
                TrendRuleInput(
                    WindowStats("Trailing 7 Days", trailing_metrics),
                    WindowStats("Year to Date", ytd_metrics),
                    WindowStats("Career", career_metrics),
                )
            )
        snapshots.append(
            PlayerSnapshot(
                player=player,
                last_night=last_night,
                trailing_7=WindowStats("Trailing 7 Days", trailing_metrics),
                ytd=WindowStats("Year to Date", ytd_metrics),
                baseline=WindowStats("Career", career_metrics),
                status=status,
            )
        )
    batters = [snapshot for snapshot in snapshots if snapshot.player.role == "batter"]
    pitchers = [snapshot for snapshot in snapshots if snapshot.player.role == "pitcher"]
    batters.sort(key=lambda snapshot: snapshot.ytd.metrics.get("hits", 0), reverse=True)
    pitchers.sort(key=lambda snapshot: snapshot.ytd.metrics.get("strikeouts", 0), reverse=True)
    return DailyReport(
        report_date=as_of_date,
        refreshed_at=datetime.now(),
        batters=batters,
        pitchers=pitchers,
    )


def write_live_report_html(output_path: Path, report: DailyReport) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_email_report_html(report), encoding="utf-8")
