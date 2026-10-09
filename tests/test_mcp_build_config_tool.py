"""Unit tests for the MCP config tool packaging helper."""

from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "mcp" / "build_mcp_config_tool.py"
    spec = importlib.util.spec_from_file_location("build_mcp_config_tool", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fake_wheel(path: Path, *, requires_dist: list[str] | None = None) -> None:
    requires = "".join(f"Requires-Dist: {requirement}\n" for requirement in requires_dist or [])
    metadata = (
        "Metadata-Version: 2.3\n"
        "Name: opamp-mcp-config\n"
        "Version: 0.6.0\n"
        f"{requires}"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("opamp_mcp_config-0.6.0.dist-info/METADATA", metadata)


def test_read_wheel_metadata_extracts_dependencies(tmp_path: Path) -> None:
    tool = _load_module()
    wheel_path = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path, requires_dist=["PyYAML>=6; extra == 'yaml'", "build>=1.2"])

    metadata = tool._read_wheel_metadata(wheel_path)

    assert metadata["name"] == "opamp-mcp-config"
    assert metadata["version"] == "0.6.0"
    assert "build>=1.2" in metadata["requires_dist"]


def test_build_sbom_payload_describes_wheel_artifact(tmp_path: Path) -> None:
    tool = _load_module()
    wheel_path = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path, requires_dist=["build>=1.2"])

    payload = tool._build_sbom_payload(wheel_path)

    assert payload["bomFormat"] == "CycloneDX"
    assert payload["specVersion"] == "1.6"
    assert payload["metadata"]["component"]["name"] == "opamp-mcp-config"
    assert payload["metadata"]["component"]["hashes"][0]["alg"] == "SHA-256"
    assert payload["dependencies"][0]["dependsOn"] == ["pkg:pypi/build"]


def test_write_sbom_creates_json_file(tmp_path: Path) -> None:
    tool = _load_module()
    wheel_path = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    sbom_path = tmp_path / "sbom" / "opamp_mcp_config.cyclonedx.json"
    _write_fake_wheel(wheel_path)

    result = tool._write_sbom(wheel_path, sbom_path)

    assert result == sbom_path
    assert json.loads(sbom_path.read_text(encoding="utf-8"))["bomFormat"] == "CycloneDX"


def test_latest_wheel_prefers_sorted_artifact(tmp_path: Path) -> None:
    tool = _load_module()
    older = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    newer = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    older.write_text("", encoding="utf-8")
    newer.write_text("", encoding="utf-8")

    assert tool._latest_wheel(tmp_path) == newer


def test_packaged_defaults_are_generated_from_source_defaults(tmp_path: Path) -> None:
    tool = _load_module()
    source_path = tmp_path / "mcp-client-defaults.json"
    packaged_path = tmp_path / "src" / "opamp_mcp_config" / "mcp-client-defaults.json"
    source_path.write_text(
        json.dumps(
            {
                "server": {"host": "localhost"},
                "deployment": {"mode": "source"},
                "clients": {},
            }
        ),
        encoding="utf-8",
    )

    original = tool._prepare_packaged_defaults(
        source_path=source_path,
        packaged_path=packaged_path,
    )
    generated = json.loads(packaged_path.read_text(encoding="utf-8"))
    tool._restore_packaged_defaults(original, packaged_path=packaged_path)

    assert original is None
    assert generated["deployment"]["mode"] == "package"
    assert not packaged_path.exists()


def test_packaged_defaults_restore_existing_file(tmp_path: Path) -> None:
    tool = _load_module()
    source_path = tmp_path / "mcp-client-defaults.json"
    packaged_path = tmp_path / "src" / "opamp_mcp_config" / "mcp-client-defaults.json"
    source_path.write_text(
        json.dumps({"deployment": {"mode": "source"}}),
        encoding="utf-8",
    )
    packaged_path.parent.mkdir(parents=True)
    packaged_path.write_text('{"existing": true}\n', encoding="utf-8")

    original = tool._prepare_packaged_defaults(
        source_path=source_path,
        packaged_path=packaged_path,
    )
    tool._restore_packaged_defaults(original, packaged_path=packaged_path)

    assert packaged_path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_cli_builds_wheel_and_sbom_without_install(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tool = _load_module()
    wheel_path = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path)
    sbom_path = tmp_path / "opamp_mcp_config.cyclonedx.json"
    calls: list[str] = []

    def fake_build_distribution(*, python_exe: str, out_dir: Path, clean: bool) -> Path:
        calls.append(f"build:{python_exe}:{out_dir}:{clean}")
        return wheel_path

    def fake_install_wheel(python_exe: str, wheel: Path) -> None:
        calls.append(f"install:{python_exe}:{wheel}")

    monkeypatch.setattr(tool, "_build_distribution", fake_build_distribution)
    monkeypatch.setattr(tool, "_install_wheel", fake_install_wheel)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_mcp_config_tool.py",
            "--python",
            "python-test",
            "--out-dir",
            str(tmp_path),
            "--sbom-path",
            str(sbom_path),
        ],
    )

    tool.main()

    captured = capsys.readouterr()
    assert "Built wheel:" in captured.out
    assert "Wrote SBOM:" in captured.out
    assert json.loads(sbom_path.read_text(encoding="utf-8"))["bomFormat"] == "CycloneDX"
    assert calls == [f"build:python-test:{tmp_path}:True"]


def test_cli_skip_sbom_and_install_invokes_pip(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tool = _load_module()
    wheel_path = tmp_path / "opamp_mcp_config-0.6.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path)
    calls: list[str] = []

    monkeypatch.setattr(
        tool,
        "_build_distribution",
        lambda *, python_exe, out_dir, clean: wheel_path,
    )
    monkeypatch.setattr(
        tool,
        "_write_sbom",
        lambda wheel, sbom: calls.append("sbom"),
    )
    monkeypatch.setattr(
        tool,
        "_install_wheel",
        lambda python_exe, wheel: calls.append(f"install:{python_exe}:{wheel}"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_mcp_config_tool.py",
            "--python",
            "python-test",
            "--out-dir",
            str(tmp_path),
            "--skip-sbom",
            "--install",
        ],
    )

    tool.main()

    captured = capsys.readouterr()
    assert "Built wheel:" in captured.out
    assert calls == [f"install:python-test:{wheel_path}"]


def test_cli_invalid_option_exits(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_module()
    monkeypatch.setattr(sys, "argv", ["build_mcp_config_tool.py", "--not-real"])

    with pytest.raises(SystemExit) as exc_info:
        tool.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "unrecognized arguments: --not-real" in captured.err
