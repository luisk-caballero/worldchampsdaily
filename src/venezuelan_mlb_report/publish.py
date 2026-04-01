from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil


def publish_static_site(report_path: Path, report_date: date, site_dir: Path) -> tuple[Path, Path]:
    site_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = site_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    latest_path = site_dir / "index.html"
    archive_path = reports_dir / f"{report_date.isoformat()}.html"

    shutil.copyfile(report_path, latest_path)
    shutil.copyfile(report_path, archive_path)
    return latest_path, archive_path
