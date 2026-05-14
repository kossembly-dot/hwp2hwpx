from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from hwp2hwpx import converter


def _write_hwpx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Contents/content.hpf", "<root />")


def _patch_java(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter, "_require_java", lambda: "java")
    monkeypatch.setattr(converter, "_jar_path", lambda: Path("fake.jar"))


def test_convert_moves_valid_hwpx(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(args, **kwargs):
        _write_hwpx(Path(args[-1]))
        return subprocess.CompletedProcess(args, 0, "", "")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    output = converter.convert(source)

    assert output == source.with_suffix(".hwpx").resolve()
    assert zipfile.is_zipfile(output)


def test_convert_fails_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(args, **kwargs):
        _write_hwpx(Path(args[-1]))
        return subprocess.CompletedProcess(args, 2, "stdout", "stderr")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="exit code 2"):
        converter.convert(source)


def test_convert_rejects_non_zip_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(args, **kwargs):
        Path(args[-1]).write_text("not a zip", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, "", "")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="valid HWPX/ZIP"):
        converter.convert(source)


def test_convert_requires_existing_input(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        converter.convert(tmp_path / "missing.hwp")


def test_convert_requires_java(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(converter, "_find_java", lambda: None)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="Java runtime not found"):
        converter.convert(source)


def test_make_ascii_tempdir_returns_ascii_path() -> None:
    tmp_dir = converter._make_ascii_tempdir()
    try:
        assert converter._is_ascii_path(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
