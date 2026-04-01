from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from venezuelan_mlb_report.models import DailyReport, PlayerSnapshot


HEADER_V_PATH = Path("/Users/lcaballer1/Documents/venezuelan-mlb-report/assets/header-marks/venezuela-v.svg")


def _format_decimal(value: float, decimals: int = 3, drop_leading_zero: bool = False) -> str:
    formatted = f"{value:.{decimals}f}"
    if drop_leading_zero and formatted.startswith("0"):
        return formatted[1:]
    return formatted


def _status_colors(status: str) -> tuple[str, str]:
    color_map = {
        "Hot": ("#ecfdf3", "#027a48"),
        "Steady": ("#eff6ff", "#175cd3"),
        "Cooling off": ("#fff7ed", "#c4320a"),
        "Slump": ("#fef3f2", "#b42318"),
    }
    return color_map.get(status, ("#f2f4f7", "#344054"))


def _header_v_markup() -> str:
    return HEADER_V_PATH.read_text(encoding="utf-8")


def _player_cell_html(snapshot: PlayerSnapshot) -> str:
    logo_html = ""
    if snapshot.player.team_logo_url:
        logo_html = (
            f"<img src='{escape(snapshot.player.team_logo_url)}' alt='{escape(snapshot.player.team)} logo' "
            "style='width:22px;height:22px;display:block;object-fit:contain;flex:0 0 auto;'>"
        )
    bg, fg = _status_colors(snapshot.status)
    return (
        "<div style='display:flex;align-items:center;gap:10px;'>"
        f"{logo_html}"
        "<div>"
        f"<div style='color:#101828;font-weight:600;white-space:nowrap;'>{escape(snapshot.player.name)}</div>"
        f"<div style='margin-top:4px;'><span style='display:inline-block;background:{bg};color:{fg};padding:3px 8px;border-radius:999px;font-size:11px;font-weight:700;'>{escape(snapshot.status)}</span></div>"
        "</div>"
        "</div>"
    )


def _project_count(value: float, games_played: float, target_games: int) -> float:
    if games_played <= 0:
        return 0.0
    return value / games_played * target_games


def _render_last_night_section(title: str, players: list[PlayerSnapshot]) -> list[str]:
    lines = [title, ""]
    rendered_any = False
    for snapshot in players:
        if snapshot.last_night is None:
            continue
        rendered_any = True
        lines.append(f"{snapshot.player.name} | {snapshot.player.team} vs {snapshot.last_night.opponent}")
        lines.append(f"Line: {snapshot.last_night.summary}")
        lines.append(f"Status: {snapshot.status}")
        lines.append(f"Note: {snapshot.last_night.commentary}")
        lines.append("")
    if not rendered_any:
        lines.append("No appearances last night.")
        lines.append("")
    return lines


def _render_metric_line(
    label: str,
    t7: float,
    ytd: float,
    career: float,
    decimals: int,
    drop_leading_zero: bool = False,
) -> str:
    return (
        f"{label}: "
        f"{_format_decimal(t7, decimals, drop_leading_zero)} T7D | "
        f"{_format_decimal(ytd, decimals, drop_leading_zero)} YTD | "
        f"{_format_decimal(career, decimals, drop_leading_zero)} Career"
    )


def _render_full_snapshot_section(
    title: str,
    players: list[PlayerSnapshot],
    metric_specs: tuple[tuple[str, str, int, bool], ...],
) -> list[str]:
    lines = [title, ""]
    for snapshot in players:
        lines.append(f"{snapshot.player.name} | {snapshot.player.team} | {snapshot.status}")
        for metric_key, metric_label, decimals, drop_leading_zero in metric_specs:
            lines.append(
                _render_metric_line(
                    metric_label,
                    snapshot.trailing_7.metrics.get(metric_key, 0.0),
                    snapshot.ytd.metrics.get(metric_key, 0.0),
                    snapshot.baseline.metrics.get(metric_key, 0.0),
                    decimals,
                    drop_leading_zero,
                )
            )
        lines.append("")
    return lines


def _render_last_night_table_html(players: list[PlayerSnapshot]) -> str:
    rows: list[str] = []
    for snapshot in players:
        if snapshot.last_night is None:
            continue
        note_html = escape(snapshot.last_night.commentary)
        if snapshot.last_night.commentary and snapshot.last_night.source_url:
            note_html = (
                f"<a href='{escape(snapshot.last_night.source_url)}' "
                "style='color:#175cd3;text-decoration:none;' target='_blank'>"
                f"{escape(snapshot.last_night.commentary)}</a>"
            )
        rows.append(
            (
                "<tr>"
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;'>{_player_cell_html(snapshot)}</td>"
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#475467;'>{escape(snapshot.last_night.opponent)}</td>"
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;white-space:nowrap;'>{escape(snapshot.last_night.summary)}</td>"
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#344054;min-width:280px;'>{note_html}</td>"
                "</tr>"
            )
        )
    if not rows:
        return (
            "<div style='background:#ffffff;border:1px solid #eaecf0;border-radius:16px;padding:20px;color:#475467;'>No appearances last night.</div>"
        )
    return (
        "<div style='background:#ffffff;border:1px solid #eaecf0;border-radius:16px;overflow-x:auto;'>"
        "<table style='width:100%;border-collapse:collapse;border-spacing:0;min-width:980px;'>"
        "<thead style='background:#f8fafc;'><tr>"
        "<th style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;'>Player</th>"
        "<th style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;'>Opponent</th>"
        "<th style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;'>Last Night</th>"
        "<th style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;'>Note</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )


def _render_snapshot_table_html(
    players: list[PlayerSnapshot],
    rate_specs: tuple[tuple[str, str, int, bool], ...],
    count_specs: tuple[tuple[str, str], ...],
    count_career_label: str,
) -> str:
    rows: list[str] = []
    for snapshot in players:
        ytd_games = snapshot.ytd.metrics.get("games", 0.0)
        projection_games = snapshot.player.projection_games_target or (162 if snapshot.player.role == "batter" else 40)
        row_cells = [
            f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;white-space:nowrap;'>{_player_cell_html(snapshot)}</td>",
            f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#475467;'>{escape(snapshot.player.team)}</td>",
        ]
        for metric_key, _, decimals, drop_leading_zero in rate_specs:
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{escape(_format_decimal(snapshot.trailing_7.metrics.get(metric_key, 0.0), decimals, drop_leading_zero))}</td>"
            )
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{escape(_format_decimal(snapshot.ytd.metrics.get(metric_key, 0.0), decimals, drop_leading_zero))}</td>"
            )
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{escape(_format_decimal(snapshot.baseline.metrics.get(metric_key, 0.0), decimals, drop_leading_zero))}</td>"
            )
        for metric_key, _ in count_specs:
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{int(round(snapshot.trailing_7.metrics.get(metric_key, 0.0)))}</td>"
            )
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{int(round(_project_count(snapshot.ytd.metrics.get(metric_key, 0.0), ytd_games, projection_games)))}</td>"
            )
            row_cells.append(
                f"<td style='padding:12px 14px;border-top:1px solid #eaecf0;color:#101828;'>{int(round(_project_count(snapshot.baseline.metrics.get(metric_key, 0.0), snapshot.baseline.metrics.get('games', 0.0), projection_games)))}</td>"
            )
        rows.append(f"<tr>{''.join(row_cells)}</tr>")
    if not rows:
        return (
            "<div style='background:#ffffff;border:1px solid #eaecf0;border-radius:16px;padding:20px;color:#475467;'>No players in this section.</div>"
        )
    return (
        "<div style='background:#ffffff;border:1px solid #eaecf0;border-radius:16px;overflow-x:auto;'>"
        "<table style='width:100%;border-collapse:collapse;border-spacing:0;min-width:1180px;'>"
        "<thead style='background:#f8fafc;'>"
        "<tr>"
        "<th rowspan='2' style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;border-bottom:1px solid #eaecf0;'>Player</th>"
        "<th rowspan='2' style='text-align:left;padding:12px 14px;color:#667085;font-size:12px;border-bottom:1px solid #eaecf0;'>Team</th>"
        + "".join(
            f"<th colspan='3' style='text-align:center;padding:12px 14px;color:#344054;font-size:12px;border-bottom:1px solid #eaecf0;'>{escape(metric_label)}</th>"
            for _, metric_label, _, _ in rate_specs
        )
        + "".join(
            f"<th colspan='3' style='text-align:center;padding:12px 14px;color:#344054;font-size:12px;border-bottom:1px solid #eaecf0;'>{escape(metric_label)}</th>"
            for _, metric_label in count_specs
        )
        + "</tr>"
        "<tr>"
        + "".join(
            "<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>T7D</th>"
            "<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>YTD</th>"
            "<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>Career</th>"
            for _ in range(len(rate_specs))
        )
        + "".join(
            "<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>T7D</th>"
            "<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>YTD Pace</th>"
            f"<th style='text-align:left;padding:10px 14px;color:#667085;font-size:12px;'>{escape(count_career_label)}</th>"
            for _ in range(len(count_specs))
        )
        + "</tr>"
        "</thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )


def render_email_report(report: DailyReport) -> str:
    long_date = report.report_date.strftime("%A, %B %-d, %Y")
    subject_date = report.report_date.strftime("%B %-d, %Y")
    sections: list[str] = [
        f"Subject: Venezuelan MLB Daily Report | {subject_date}",
        "",
        "Venezuelan MLB Daily Report",
        long_date,
        "",
    ]
    sections.extend(_render_last_night_section("BATTERS: LAST NIGHT", report.batters))
    sections.extend(_render_last_night_section("STARTING PITCHERS: LAST NIGHT", [p for p in report.pitchers if p.player.subrole == "starter"]))
    sections.extend(_render_last_night_section("RELIEF PITCHERS: LAST NIGHT", [p for p in report.pitchers if p.player.subrole == "reliever"]))
    sections.extend(
        _render_full_snapshot_section(
            "BATTERS: FULL SNAPSHOT",
            report.batters,
            (
                ("avg", "AVG", 3, True),
                ("ops", "OPS", 3, True),
            ),
        )
    )
    sections.extend(
        _render_full_snapshot_section(
            "STARTING PITCHERS: FULL SNAPSHOT",
            [p for p in report.pitchers if p.player.subrole == "starter"],
            (
                ("era", "ERA", 2, False),
                ("whip", "WHIP", 2, False),
                ("k_per_9", "K/9", 1, False),
            ),
        )
    )
    sections.extend(
        _render_full_snapshot_section(
            "RELIEF PITCHERS: FULL SNAPSHOT",
            [p for p in report.pitchers if p.player.subrole == "reliever"],
            (
                ("era", "ERA", 2, False),
                ("whip", "WHIP", 2, False),
                ("k_per_9", "K/9", 1, False),
            ),
        )
    )
    return "\n".join(sections).rstrip() + "\n"


def render_email_report_html(report: DailyReport) -> str:
    long_date = report.report_date.strftime("%A, %B %-d, %Y")
    subject_date = report.report_date.strftime("%B %-d, %Y")
    refreshed_text = ""
    if report.refreshed_at is not None:
        refreshed_text = report.refreshed_at.strftime("%I:%M %p").lstrip("0")
    starters = [snapshot for snapshot in report.pitchers if snapshot.player.subrole == "starter"]
    relievers = [snapshot for snapshot in report.pitchers if snapshot.player.subrole == "reliever"]
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Venezuelan MLB Daily Report | {escape(subject_date)}</title>
  </head>
  <body style="margin:0;padding:0;background:#f4f7fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#101828;">
    <div style="display:none;max-height:0;overflow:hidden;">Venezuelan MLB Daily Report for {escape(subject_date)}</div>
    <div style="max-width:1180px;margin:0 auto;padding:32px 20px 48px 20px;">
      <div style="background:linear-gradient(135deg, #2b0f1a 0%, #8b1e2d 58%, #1d4ed8 100%);border-radius:24px;padding:28px 28px 30px 28px;color:#ffffff;">
        <div style="display:flex;align-items:center;gap:18px;">
          <div style="width:68px;height:68px;background:#ffffff;border-radius:16px;padding:8px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
            {_header_v_markup()}
          </div>
          <div>
            <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;opacity:0.85;">Daily Digest</div>
            <h1 style="margin:8px 0 6px 0;font-size:32px;line-height:38px;">Venezuelan MLB Daily Report</h1>
            <div style="font-size:15px;line-height:22px;opacity:0.9;">{escape(long_date)}</div>
            <div style="font-size:13px;line-height:20px;opacity:0.82;margin-top:4px;">Last refreshed: {escape(refreshed_text)} ET</div>
          </div>
        </div>
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Batters: Last Night</h2>
        {_render_last_night_table_html(report.batters)}
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Starting Pitchers: Last Night</h2>
        {_render_last_night_table_html(starters)}
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Relief Pitchers: Last Night</h2>
        {_render_last_night_table_html(relievers)}
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Batters: Full Snapshot</h2>
        <div style="font-size:13px;line-height:20px;color:#475467;margin:0 0 12px 0;">Rate stats show current values. Counting stats show trailing 7-day totals, plus full-season pace from YTD and career.</div>
        {_render_snapshot_table_html(
            report.batters,
            (
                ("avg", "AVG", 3, True),
                ("ops", "OPS", 3, True),
            ),
            (
                ("hits", "Hits"),
                ("xbh", "XBH"),
                ("hr", "HR"),
            ),
            "Career /162",
        )}
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Starting Pitchers: Full Snapshot</h2>
        <div style="font-size:13px;line-height:20px;color:#475467;margin:0 0 12px 0;">Rate stats show current values. Counting stats show trailing 7-day totals, plus full-season pace from YTD and career.</div>
        {_render_snapshot_table_html(
            starters,
            (
                ("era", "ERA", 2, False),
                ("whip", "WHIP", 2, False),
                ("k_per_9", "K/9", 1, False),
            ),
            (
                ("strikeouts", "Strikeouts"),
                ("wins", "Wins"),
            ),
            "Career /Season",
        )}
      </div>

      <div style="margin-top:28px;">
        <h2 style="font-size:22px;line-height:30px;color:#101828;margin:0 0 16px 0;">Relief Pitchers: Full Snapshot</h2>
        <div style="font-size:13px;line-height:20px;color:#475467;margin:0 0 12px 0;">Rate stats show current values. Counting stats show trailing 7-day totals, plus full-season pace from YTD and career.</div>
        {_render_snapshot_table_html(
            relievers,
            (
                ("era", "ERA", 2, False),
                ("whip", "WHIP", 2, False),
                ("k_per_9", "K/9", 1, False),
            ),
            (
                ("strikeouts", "Strikeouts"),
                ("saves", "Saves"),
            ),
            "Career /Season",
        )}
      </div>
    </div>
  </body>
</html>
"""


def default_report_date() -> date:
    return date.today()
