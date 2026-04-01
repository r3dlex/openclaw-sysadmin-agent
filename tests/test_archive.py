"""Unit tests for tools.archive — memory file archiving logic."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools import archive


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_old_file(tmp_path: Path, name: str, days_old: int) -> Path:
    """Create a .md file in tmp_path with an mtime `days_old` days in the past."""
    p = tmp_path / name
    p.write_text(f"# {name}\nContent.")
    old_mtime = (datetime.now() - timedelta(days=days_old)).timestamp()
    import os
    os.utime(str(p), (old_mtime, old_mtime))
    return p


# ---------------------------------------------------------------------------
# main() — core archiving logic
# ---------------------------------------------------------------------------


class TestArchiveMain:
    """Tests for tools.archive.main()."""

    def test_archives_old_md_file(self, tmp_path: Path) -> None:
        """Files older than threshold are moved to archive dir."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "archive"

        _make_old_file(memory_dir, "old_note.md", days_old=40)

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()

        assert not (memory_dir / "old_note.md").exists()
        assert (archive_dir / "old_note.md").exists()

    def test_keeps_recent_md_file(self, tmp_path: Path) -> None:
        """Files newer than threshold are left in place."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "archive"

        _make_old_file(memory_dir, "recent.md", days_old=5)

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()

        assert (memory_dir / "recent.md").exists()
        assert not (archive_dir / "recent.md").exists() if archive_dir.exists() else True

    def test_skips_non_md_files(self, tmp_path: Path) -> None:
        """Non-.md files are ignored even if they are old."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "archive"

        txt_file = memory_dir / "old_file.txt"
        txt_file.write_text("not markdown")
        import os
        old_mtime = (datetime.now() - timedelta(days=60)).timestamp()
        os.utime(str(txt_file), (old_mtime, old_mtime))

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()

        assert (memory_dir / "old_file.txt").exists()

    def test_missing_memory_dir_returns_early(self, tmp_path: Path) -> None:
        """main() returns early when memory dir does not exist — no crash."""
        memory_dir = tmp_path / "nonexistent_memory"
        archive_dir = tmp_path / "archive"

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()  # must not raise

    def test_creates_archive_dir_when_missing(self, tmp_path: Path) -> None:
        """Archive directory is created if it doesn't exist."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "deep" / "nested" / "archive"

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()

        assert archive_dir.exists()

    def test_archives_multiple_old_files(self, tmp_path: Path) -> None:
        """All old .md files are archived, recent ones are kept."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "archive"

        _make_old_file(memory_dir, "old1.md", days_old=35)
        _make_old_file(memory_dir, "old2.md", days_old=60)
        _make_old_file(memory_dir, "recent.md", days_old=1)

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", 30),
        ):
            archive.main()

        assert (archive_dir / "old1.md").exists()
        assert (archive_dir / "old2.md").exists()
        assert (memory_dir / "recent.md").exists()

    @pytest.mark.parametrize("days_old,threshold,should_archive", [
        (31, 30, True),
        (30, 30, True),    # exactly at threshold — archived (mtime < cutoff uses timedelta subtraction)
        (29, 30, False),
        (0, 30, False),
        (100, 90, True),
        (89, 90, False),
    ])
    def test_threshold_boundary(
        self, tmp_path: Path, days_old: int, threshold: int, should_archive: bool
    ) -> None:
        """Parametrized threshold boundary conditions."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        archive_dir = tmp_path / "archive"

        _make_old_file(memory_dir, "file.md", days_old=days_old)

        with (
            patch.object(archive, "MEMORY_DIR", memory_dir),
            patch.object(archive, "ARCHIVE_DIR", archive_dir),
            patch.object(archive, "DAYS_THRESHOLD", threshold),
        ):
            archive.main()

        archived = (archive_dir / "file.md").exists()
        assert archived == should_archive, (
            f"days_old={days_old}, threshold={threshold}: expected archived={should_archive}"
        )
