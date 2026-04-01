from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from venezuelan_mlb_report.ingest import (
    build_historical_snapshots,
    build_live_snapshots,
    write_historical_snapshots,
    write_snapshots,
)
from venezuelan_mlb_report.live_report import build_live_daily_report, write_live_report_html
from venezuelan_mlb_report.publish import publish_static_site
from venezuelan_mlb_report.report import render_email_report, render_email_report_html
from venezuelan_mlb_report.sample_data import build_sample_report
from venezuelan_mlb_report.storage import init_db
from venezuelan_mlb_report.universe import load_tracking_rules, load_universe, select_seed_players


DEFAULT_DB_PATH = Path("var/report.db")


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


if __name__ == "__main__":
    main()
