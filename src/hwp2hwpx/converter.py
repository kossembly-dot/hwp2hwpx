"""Core conversion logic — calls bundled JAR via subprocess."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Union

_java_exe: Optional[str] = None  # cached after first lookup


def _jar_path() -> Path:
    return Path(__file__).parent / "jars" / "hwp2hwpx.jar"


def _find_java() -> Optional[str]:
    """Find java executable — PATH, JAVA_HOME, then common install dirs."""
    global _java_exe
    if _java_exe is not None:
        return _java_exe

    def _works(cmd: str) -> bool:
        try:
            subprocess.run(
                [cmd, "-version"], capture_output=True, timeout=15,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    # 1) PATH (refresh on Windows — new installs may not be in current session)
    if platform.system() == "Windows":
        import ctypes
        try:
            machine = os.environ.get("Path", "")
            fresh = ctypes.windll.kernel32  # type: ignore[attr-defined]
            # Simpler: read registry-level PATH
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ) as key:
                machine, _ = winreg.QueryValueEx(key, "Path")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                user, _ = winreg.QueryValueEx(key, "Path")
            os.environ["Path"] = machine + ";" + user
        except Exception:
            pass

    if _works("java"):
        _java_exe = "java"
        return _java_exe

    # 2) JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = os.path.join(java_home, "bin", "java")
        if _works(candidate):
            _java_exe = candidate
            return _java_exe

    # 3) Common Windows install directories
    if platform.system() == "Windows":
        for base in [
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Java",
            r"C:\Program Files\Microsoft",
            r"C:\Program Files\Zulu",
        ]:
            if not os.path.isdir(base):
                continue
            for d in sorted(os.listdir(base), reverse=True):
                candidate = os.path.join(base, d, "bin", "java.exe")
                if os.path.isfile(candidate) and _works(candidate):
                    _java_exe = candidate
                    return _java_exe

    return None


def check_java() -> bool:
    """Check if Java runtime is available.

    Returns:
        True if a working ``java`` executable is found.
    """
    return _find_java() is not None


def _require_java() -> str:
    """Return java executable path, or raise with install instructions."""
    java = _find_java()
    if java is None:
        raise RuntimeError(
            "Java runtime not found. Install JRE 8+ to use hwp2hwpx.\n"
            "  Windows : winget install EclipseAdoptium.Temurin.21.JDK\n"
            "  macOS   : brew install temurin\n"
            "  Linux   : apt install default-jre"
        )
    return java


def convert(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    *,
    timeout: int = 120,
) -> Path:
    """Convert a single HWP file to HWPX.

    Uses temporary files with ASCII-only paths internally so that
    Korean (or other non-ASCII) file paths never reach the JVM,
    avoiding encoding issues on Windows.

    Args:
        input_path: Path to the ``.hwp`` file.
        output_path: Where to write the ``.hwpx`` file.
            Defaults to the same directory and base name.
        timeout: Subprocess timeout in seconds.

    Returns:
        Resolved :class:`~pathlib.Path` of the created ``.hwpx`` file.

    Raises:
        FileNotFoundError: *input_path* does not exist.
        RuntimeError: Java is missing or conversion failed.
    """
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".hwpx")
    output_path = Path(output_path).resolve()

    java = _require_java()
    jar = _jar_path()

    # Temp dir with ASCII-only paths (Korean path workaround)
    tmp_dir = Path(tempfile.mkdtemp(prefix="hwp2hwpx_"))
    tmp_in = tmp_dir / "input.hwp"
    tmp_out = tmp_dir / "output.hwpx"

    try:
        shutil.copy2(input_path, tmp_in)

        result = subprocess.run(
            [
                java,
                "-Dfile.encoding=UTF-8",
                "-jar",
                str(jar),
                str(tmp_in),
                str(tmp_out),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if not tmp_out.exists():
            detail = (result.stderr or result.stdout or "no output").strip()
            raise RuntimeError(f"Conversion failed: {detail}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_out), str(output_path))
        return output_path

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def convert_batch(
    paths: List[Union[str, Path]],
    output_dir: Optional[Union[str, Path]] = None,
    *,
    timeout: int = 120,
) -> list[tuple[Path, Optional[Path], Optional[str]]]:
    """Convert multiple HWP files.

    Args:
        paths: HWP file paths.
        output_dir: Common output directory. ``None`` = same as each input.
        timeout: Per-file subprocess timeout.

    Returns:
        List of ``(input, output_or_None, error_or_None)`` tuples.
    """
    _require_java()  # fail-fast before processing any files

    results: list[tuple[Path, Optional[Path], Optional[str]]] = []
    for p in paths:
        p = Path(p)
        out = Path(output_dir) / (p.stem + ".hwpx") if output_dir else None
        try:
            created = convert(p, out, timeout=timeout)
            results.append((p, created, None))
        except Exception as exc:
            results.append((p, None, str(exc)))
    return results
