from __future__ import annotations

from pathlib import Path

import pytest

from hwp2hwpx import cli


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])

    assert exc_info.value.code == 0
    assert "hwp2hwpx 1.0.0" in capsys.readouterr().out


def test_no_files_found_exits_with_error(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(tmp_path / "*.hwp")])

    assert exc_info.value.code == 1
    assert "No HWP files found." in capsys.readouterr().err


def test_recursive_conversion_uses_output_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "docs" / "nested" / "sample.hwp"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"hwp")
    output_dir = tmp_path / "out"
    seen: list[tuple[Path, Path | None]] = []

    def fake_convert(input_path, output_path=None):
        output = Path(output_path) if output_path else Path(input_path).with_suffix(".hwpx")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"x" * 1024)
        seen.append((Path(input_path), output))
        return output

    monkeypatch.setattr(cli, "convert", fake_convert)

    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(tmp_path / "docs"), "-r", "-o", str(output_dir)])

    assert exc_info.value.code == 0
    assert seen == [(source, output_dir / "sample.hwpx")]
