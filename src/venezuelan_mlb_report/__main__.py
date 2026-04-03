from __future__ import annotations

import argparse
import subprocess
import time
from datetime import date, datetime
from pathlib import Path

from venezuelan_mlb_report.ingest import (
    build_historical_snapshots,
    build_live_snapshots,
    write_historical_snapshots,
    write_snapshots,
)
from venezuelan_mlb_report.live_report import build_live_daily_report, write_live_report_html
from venezuelan_mlb_report.mlb_api import MLBApiError
from venezuelan_mlb_report.publish import publish_static_site
from venezuelan_mlb_report.report import render_email_report, render_email_report_html
from venezuelan_mlb_report.sample_data import build_sample_report
from venezuelan_mlb_report.storage import init_db
from venezuelan_mlb_report.universe import load_tracking_rules, load_universe, select_seed_players


DEFAULT_DB_PATH = Path("var/report.db")


def _run_git(repo_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=False,
        text=True,
        capture_output=True,
    )


def _push_site_updates(repo_dir: Path, report_date: date, commit_message: str) -> bool:
    add_result = _run_git(repo_dir, "add", "site")
    if add_result.returncode != 0:
        raise RuntimeError(add_result.stderr.strip() or "Failed to stage site output")

    diff_result = _run_git(repo_dir, "diff", "--cached", "--quiet", "--", "site")
    if diff_result.returncode == 0:
        print("No site changes detected; skipping git commit and push.")
        return False
    if diff_result.returncode not in (0, 1):
        raise RuntimeError(diff_result.stderr.strip() or "Failed to inspect staged site changes")

    commit_result = _run_git(repo_dir, "commit", "-m", commit_message.format(report_date=report_date.isoformat()))
    if commit_result.returncode != 0:
        raise RuntimeError(commit_result.stderr.strip() or "Failed to commit site changes")
    if commit_result.stdout.strip():
        print(commit_result.stdout.strip())

    push_result = _run_git(repo_dir, "push", "origin", "HEAD")
    if push_result.returncode != 0:
        raise RuntimeError(push_result.stderr.strip() or "Failed to push site changes")
    if push_result.stdout.strip():
        print(push_result.stdout.strip())
    if push_result.stderr.strip():
        print(push_result.stderr.strip())
    return True


def _run_daily_once(
    *,
    report_date: date,
    season: int,
    tiers: tuple[str, ...],
    live_output: Path,
    history_output: Path,
    history_start: int,
    history_mode: str,
    report_output: Path,
    publish_site_dir: Path,
) -> None:
    universe = load_universe()
    tracking_rules = load_tracking_rules()
    selected_players = select_seed_players(universe, tiers)

    live_snapshots = build_live_snapshots(selected_players, tracking_rules, season)
    write_snapshots(live_output, live_snapshots)
    print(f"Wrote {len(live_snapshots)} live player snapshots to {live_output}")

    history_needed = history_mode == "refresh" or (
        history_mode == "if-missing" and not history_output.exists()
    )
    if history_needed:
        history_end = season - 1
        historical_snapshots = build_historical_snapshots(selected_players, history_start, history_end)
        write_historical_snapshots(history_output, historical_snapshots)
        print(f"Wrote {len(historical_snapshots)} historical season snapshots to {history_output}")
    elif history_mode == "skip" and not history_output.exists():
        raise FileNotFoundError(f"History file not found: {history_output}")
    else:
        print(f"Using existing historical snapshots at {history_output}")

    report = build_live_daily_report(
        live_path=live_output,
        historical_path=history_output,
        as_of_date=report_date,
        season=season,
    )
    write_live_report_html(report_output, report)
    latest_path, archive_path = publish_static_site(report_output, report_date, publish_site_dir)
    print(f"Published site latest page to {latest_path}")
    print(f"Published site archive page to {archive_path}")
    print(f"Wrote live HTML report to {report_output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Venezuelan MLB daily report tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Initialize the SQLite database")
    init_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)

    sample_parser = subparsers.add_parser("sample-report", help="Render a sample daily report")
    sample_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    sample_parser.add_argument("--format", choices=("text", "html"), default="text")
    sample_parser.add_argument("--output", type=Path)

    pull_parser = subparsers.add_parser("pull-live", help="Pull live season stats for selected seed players")
    pull_parser.add_argument("--season", type=int, required=True)
    pull_parser.add_argument("--tiers", nargs="+", default=["core", "active"])
    pull_parser.add_argument("--output", type=Path, default=Path("var/live_player_stats.json"))

    history_parser = subparsers.add_parser("backfill-history", help="Pull historical season stats for selected seed players")
    history_parser.add_argument("--season-start", type=int, required=True)
    history_parser.add_argument("--season-end", type=int, required=True)
    history_parser.add_argument("--tiers", nargs="+", default=["core", "active"])
    history_parser.add_argument("--output", type=Path, default=Path("var/historical_player_stats.json"))

    report_parser = subparsers.add_parser("build-live-report", help="Build an HTML report from live and historical data")
    report_parser.add_argument("--season", type=int, required=True)
    report_parser.add_argument("--as-of-date", type=str, required=True)
    report_parser.add_argument("--live-input", type=Path, default=Path("var/live_player_stats.json"))
    report_parser.add_argument("--history-input", type=Path, default=Path("var/historical_player_stats.json"))
    report_parser.add_argument("--output", type=Path, default=Path("var/live_report.html"))
    report_parser.add_argument("--publish-site-dir", type=Path)

    daily_parser = subparsers.add_parser("run-daily", help="Run the full daily pipeline and optionally push the site")
    daily_parser.add_argument("--season", type=int)
    daily_parser.add_argument("--as-of-date", type=str)
    daily_parser.add_argument("--tiers", nargs="+", default=["core", "active"])
    daily_parser.add_argument("--live-output", type=Path, default=Path("var/live_player_stats.json"))
    daily_parser.add_argument("--history-output", type=Path, default=Path("var/historical_player_stats_full.json"))
    daily_parser.add_argument("--history-start", type=int, default=2010)
    daily_parser.add_argument("--history-mode", choices=("if-missing", "refresh", "skip"), default="if-missing")
    daily_parser.add_argument("--report-output", type=Path, default=Path("var/live_report.html"))
    daily_parser.add_argument("--publish-site-dir", type=Path, default=Path("site"))
    daily_parser.add_argument("--git-push", action="store_true")
    daily_parser.add_argument("--max-attempts", type=int, default=3)
    daily_parser.add_argument("--retry-delay-seconds", type=int, default=60)
    daily_parser.add_argument("--repo-dir", type=Path, default=Path("."))
    daily_parser.add_argument(
        "--commit-message",
        default="Update daily report for {report_date}",
        help="Git commit message template. Use {report_date} for the report date.",
    )

    args = parser.parse_args()

    if args.command == "init-db":
        init_db(args.db_path)
        print(f"Initialized database at {args.db_path}")
        return

    if args.command == "sample-report":
        report = build_sample_report()
        rendered = render_email_report(report) if args.format == "text" else render_email_report_html(report)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote {args.format} sample report to {args.output}")
            return
        print(rendered)
        return

    if args.command == "pull-live":
        universe = load_universe()
        tracking_rules = load_tracking_rules()
        selected_players = select_seed_players(universe, tuple(args.tiers))
        snapshots = build_live_snapshots(selected_players, tracking_rules, args.season)
        write_snapshots(args.output, snapshots)
        print(f"Wrote {len(snapshots)} live player snapshots to {args.output}")
        return

    if args.command == "backfill-history":
        universe = load_universe()
        selected_players = select_seed_players(universe, tuple(args.tiers))
        snapshots = build_historical_snapshots(selected_players, args.season_start, args.season_end)
        write_historical_snapshots(args.output, snapshots)
        print(
            f"Wrote {len(snapshots)} historical season snapshots to {args.output}"
        )
        return

    if args.command == "build-live-report":
        report_date = datetime.strptime(args.as_of_date, "%Y-%m-%d").date()
        report = build_live_daily_report(
            live_path=args.live_input,
            historical_path=args.history_input,
            as_of_date=report_date,
            season=args.season,
        )
        write_live_report_html(args.output, report)
        if args.publish_site_dir:
            latest_path, archive_path = publish_static_site(args.output, report_date, args.publish_site_dir)
            print(f"Published site latest page to {latest_path}")
            print(f"Published site archive page to {archive_path}")
        print(f"Wrote live HTML report to {args.output}")
        return

    if args.command == "run-daily":
        report_date = datetime.strptime(args.as_of_date, "%Y-%m-%d").date() if args.as_of_date else date.today()
        season = args.season or report_date.year
        attempts = max(1, args.max_attempts)
        retryable_exceptions = (MLBApiError, TimeoutError)

        for attempt in range(1, attempts + 1):
            try:
                _run_daily_once(
                    report_date=report_date,
                    season=season,
                    tiers=tuple(args.tiers),
                    live_output=args.live_output,
                    history_output=args.history_output,
                    history_start=args.history_start,
                    history_mode=args.history_mode,
                    report_output=args.report_output,
                    publish_site_dir=args.publish_site_dir,
                )
                break
            except retryable_exceptions as exc:
                if attempt >= attempts:
                    raise
                delay_seconds = max(1, args.retry_delay_seconds) * attempt
                print(
                    f"Run attempt {attempt}/{attempts} failed with retryable error: {exc}. "
                    f"Retrying in {delay_seconds} seconds..."
                )
                time.sleep(delay_seconds)

        if args.git_push:
            pushed = _push_site_updates(args.repo_dir.resolve(), report_date, args.commit_message)
            if pushed:
                print("Pushed updated site output to GitHub.")
        return


if __name__ == "__main__":
    main()
