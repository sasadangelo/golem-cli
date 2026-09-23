"""Unit tests for agent init and list commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from golem_cli.cli import app
from golem_cli.commands.agent_command import AgentCommand


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_agent_init_creates_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    golem_path = tmp_path / ".golem"
    monkeypatch.setattr("golem_cli.config.GOLEM_PATH", golem_path)

    cmd = AgentCommand(base_url="http://localhost:9000")
    cmd.init("myapp")

    workspace_dir = golem_path / "agents" / "myapp"
    assert workspace_dir.exists()
    assert (workspace_dir / "skills").is_dir()
    assert (workspace_dir / "AGENTS.md").is_file()
    assert (workspace_dir / "AGENTS.md").read_text() == "You are a helpful assistant.\n"
    assert (workspace_dir / "config.yaml").is_file()

    raw_config = yaml.safe_load((workspace_dir / "config.yaml").read_text())
    assert raw_config["agent"]["id"] == "myapp"
    assert raw_config["agent"]["name"] == "myapp"
    assert raw_config["agent"]["version"] == "0.2.0"


def test_agent_init_already_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    golem_path = tmp_path / ".golem"
    monkeypatch.setattr("golem_cli.config.GOLEM_PATH", golem_path)

    workspace_dir = golem_path / "agents" / "myapp"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    custom_file = workspace_dir / "custom.txt"
    custom_file.write_text("custom")

    cmd = AgentCommand(base_url="http://localhost:9000")
    cmd.init("myapp")

    # Should not overwrite or fail
    assert custom_file.exists()
    assert not (workspace_dir / "config.yaml").exists()


def test_agent_list_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    golem_path = tmp_path / ".golem"
    monkeypatch.setattr("golem_cli.config.GOLEM_PATH", golem_path)

    cmd = AgentCommand(base_url="http://localhost:9000")
    cmd.list()

    captured = capsys.readouterr()
    assert "No agents found." in captured.out


def test_agent_list_scans_workspaces_stopped_and_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    golem_path = tmp_path / ".golem"
    monkeypatch.setattr("golem_cli.config.GOLEM_PATH", golem_path)

    cmd = AgentCommand(base_url="http://localhost:9000")
    cmd.init("default")
    cmd.init("sre-bot")
    capsys.readouterr()  # clear init output

    # Mock CP call returning default as running
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"agent_id": "default", "status": "RUNNING"}]

    with patch.object(cmd.client, "get", return_value=mock_resp):
        cmd.list()

    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert "NAME        ID          VERSION   STATUS" in lines[0]
    assert any("default" in line and "0.2.0" in line and "RUNNING" in line for line in lines)
    assert any("sre-bot" in line and "0.2.0" in line and "STOPPED" in line for line in lines)


def test_cli_agent_init_and_list_integration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
) -> None:
    golem_path = tmp_path / ".golem"
    monkeypatch.setattr("golem_cli.config.GOLEM_PATH", golem_path)

    # golem agent init testagent
    res = cli_runner.invoke(app, ["agent", "init", "testagent"])
    assert res.exit_code == 0
    assert "Agent workspace 'testagent' initialized" in res.stdout

    # golem agent init testagent again
    res2 = cli_runner.invoke(app, ["agent", "init", "testagent"])
    assert res2.exit_code == 0
    assert "already exists" in res2.stdout or "already exists" in res2.stderr

    # golem agent list without CP
    res3 = cli_runner.invoke(app, ["agent", "list"])
    assert res3.exit_code == 0
    assert "testagent" in res3.stdout
    assert "0.2.0" in res3.stdout
    assert "STOPPED" in res3.stdout
