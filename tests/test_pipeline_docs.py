"""Unit tests for tools.pipeline_runner.pipelines.docs."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tools.pipeline_runner.pipelines import docs
from tools.pipeline_runner.runner import PipelineResult


# ---------------------------------------------------------------------------
# _check_internal_links()
# ---------------------------------------------------------------------------


class TestCheckInternalLinks:
    def test_no_warnings_when_links_resolve(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# Target")
        md_file = tmp_path / "source.md"
        md_file.write_text("[link](target.md)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert errors == []
        assert warnings == []

    def test_warning_when_link_broken(self, tmp_path: Path) -> None:
        md_file = tmp_path / "source.md"
        md_file.write_text("[broken link](nonexistent.md)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert errors == []
        assert any("nonexistent.md" in w for w in warnings)

    def test_skips_http_links(self, tmp_path: Path) -> None:
        md_file = tmp_path / "source.md"
        md_file.write_text("[external](https://example.com/page)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert warnings == []

    def test_skips_anchor_only_links(self, tmp_path: Path) -> None:
        md_file = tmp_path / "source.md"
        md_file.write_text("[anchor](#section-heading)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert warnings == []

    def test_skips_mailto_links(self, tmp_path: Path) -> None:
        md_file = tmp_path / "source.md"
        md_file.write_text("[email](mailto:test@example.com)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert warnings == []

    def test_handles_anchor_in_path(self, tmp_path: Path) -> None:
        """path#anchor should check path part only."""
        target = tmp_path / "doc.md"
        target.write_text("# Doc")
        md_file = tmp_path / "source.md"
        md_file.write_text("[with anchor](doc.md#section)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert warnings == []

    def test_no_false_positive_for_bare_word_link(self, tmp_path: Path) -> None:
        """Links that are bare words without / or . are skipped."""
        md_file = tmp_path / "source.md"
        md_file.write_text("[word link](justword)")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_internal_links()
        assert warnings == []


# ---------------------------------------------------------------------------
# _check_todo_markers()
# ---------------------------------------------------------------------------


class TestCheckTodoMarkers:
    def test_warns_on_todo(self, tmp_path: Path) -> None:
        md_file = tmp_path / "notes.md"
        md_file.write_text("# Notes\nTODO: fix this later\n")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert any("TODO" in w for w in warnings)

    def test_warns_on_fixme(self, tmp_path: Path) -> None:
        md_file = tmp_path / "notes.md"
        md_file.write_text("# Notes\nFIXME: broken logic\n")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert any("FIXME" in w for w in warnings)

    def test_no_warnings_when_clean(self, tmp_path: Path) -> None:
        md_file = tmp_path / "clean.md"
        md_file.write_text("# Clean doc\nNo markers here.\n")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert warnings == []

    def test_skips_todo_in_code_block(self, tmp_path: Path) -> None:
        content = "# Doc\n```\nTODO: this is in a code block\n```\n"
        md_file = tmp_path / "with_code.md"
        md_file.write_text(content)

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert warnings == []

    def test_skips_excluded_files(self, tmp_path: Path) -> None:
        """PIPELINES.md, TESTING.md, ARCHITECTURE.md are excluded."""
        for name in {"PIPELINES.md", "TESTING.md", "ARCHITECTURE.md"}:
            (tmp_path / name).write_text("# TODO: intentional\n")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert warnings == []

    @pytest.mark.parametrize("marker", ["TODO", "FIXME", "HACK", "XXX"])
    def test_all_marker_types_caught(self, tmp_path: Path, marker: str) -> None:
        md_file = tmp_path / "notes.md"
        md_file.write_text(f"# Notes\n{marker}: something\n")

        with patch.object(docs, "REPO_ROOT", tmp_path):
            errors, warnings = docs._check_todo_markers()
        assert any(marker in w for w in warnings)


# ---------------------------------------------------------------------------
# run() — full docs pipeline
# ---------------------------------------------------------------------------


class TestDocsPipelineRun:
    def test_passes_when_no_errors(self, tmp_path: Path) -> None:
        with (
            patch.object(docs, "_check_internal_links", return_value=([], [])),
            patch.object(docs, "_check_todo_markers", return_value=([], [])),
        ):
            result = docs.run()
        assert result.passed is True

    def test_passes_with_warnings_only(self) -> None:
        with (
            patch.object(docs, "_check_internal_links", return_value=([], ["broken link"])),
            patch.object(docs, "_check_todo_markers", return_value=([], [])),
        ):
            result = docs.run()
        assert result.passed is True
        assert "broken link" in result.warnings

    def test_fails_when_errors_present(self) -> None:
        with (
            patch.object(docs, "_check_internal_links", return_value=(["error!"], [])),
            patch.object(docs, "_check_todo_markers", return_value=([], [])),
        ):
            result = docs.run()
        assert result.passed is False

    def test_exception_adds_error(self) -> None:
        with (
            patch.object(docs, "_check_internal_links", side_effect=RuntimeError("oops")),
            patch.object(docs, "_check_todo_markers", return_value=([], [])),
        ):
            result = docs.run()
        assert result.passed is False
        assert any("oops" in e for e in result.errors)

    def test_result_name_is_docs(self) -> None:
        with (
            patch.object(docs, "_check_internal_links", return_value=([], [])),
            patch.object(docs, "_check_todo_markers", return_value=([], [])),
        ):
            result = docs.run()
        assert result.name == "Docs"
