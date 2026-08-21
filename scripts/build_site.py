#!/usr/bin/env python3
"""Build an allowlisted static-site directory for local serving and deployment."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable


SITE_FILES = (
    "index.html",
    "video_viewer.html",
    "editor.html",
    "music_viewer.html",
    "manual_video_editor.html",
    "alias_editor.html",
    "assets/editor.css",
    "assets/editor_shared.js",
    "assets/manual_video_editor.js",
    "assets/alias_editor.js",
    "assets/staff_review_editor.js",
    "assets/editor_bootstrap.js",
    "assets/index.css",
    "assets/index.js",
    "assets/viewer_controls.css",
    "assets/viewer_controls.js",
    "assets/video_viewer.css",
    "assets/video_viewer.js",
    "assets/legacy_redirect.js",
    "assets/legacy_redirect.css",
    "output/combined_music_data.json",
    "output/database_v2.json",
    "output/aliases.json",
    "output/original_mv_review.json",
    "output/staff_review.json",
    "manual_data/manual_videos.json",
    "manual_data/original_video_overrides.json",
    "manual_data/staff_role_aliases.json",
    "manual_data/staff_name_aliases.json",
    "manual_data/staff_line_ignores.json",
    "sekai-master-db-diff-main/gameCharacters.json",
    "sekai-master-db-diff-main/outsideCharacters.json",
)


def copy_site_files(base_path: Path, staging_dir: Path, relative_paths: Iterable[str]) -> None:
    for relative_path in relative_paths:
        source = base_path / relative_path
        if not source.is_file():
            raise FileNotFoundError(f"站点缺少必需文件: {relative_path}")
        target = staging_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def build_site(base_path: Path | None = None, dist_dir: Path | None = None) -> Path:
    base_path = (base_path or Path(__file__).resolve().parents[1]).resolve()
    dist_dir = (dist_dir or base_path / "dist").resolve()
    if dist_dir == base_path or base_path not in dist_dir.parents:
        raise ValueError("dist 目录必须位于项目目录内，且不能是项目根目录")

    staging_dir = Path(tempfile.mkdtemp(prefix=".site-staging-", dir=str(base_path)))
    previous_dir = Path(tempfile.mkdtemp(prefix=".site-previous-", dir=str(base_path)))
    previous_dir.rmdir()
    moved_previous = False
    try:
        copy_site_files(base_path, staging_dir, SITE_FILES)
        if dist_dir.exists():
            os.replace(dist_dir, previous_dir)
            moved_previous = True
        os.replace(staging_dir, dist_dir)
        if moved_previous:
            shutil.rmtree(previous_dir, ignore_errors=True)
        return dist_dir
    except Exception:
        if moved_previous and previous_dir.exists() and not dist_dir.exists():
            os.replace(previous_dir, dist_dir)
        raise
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
        shutil.rmtree(previous_dir, ignore_errors=True)


def main() -> int:
    output = build_site()
    print(f"[OK] 静态站点已生成: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
