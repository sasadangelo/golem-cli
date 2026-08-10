"""Agent command — agent sandbox lifecycle and runner-config template."""

from pathlib import Path

import httpx
import typer
import yaml

from golem_cli import config as cfg
from golem_cli.models import RunnerConfig

from ._agent_config_template import write_default
from .base import Command


class AgentCommand(Command):
    """Encapsulates all agent lifecycle and agent-config operations."""

    def __init__(self) -> None:
        self._base_url = cfg.get_active_url()
        self._client = httpx.Client(base_url=self._base_url, timeout=30)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Raise a clean typer.Exit on HTTP errors, surfacing the response body."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            detail = f": {body}" if body else ""
            typer.echo(
                f"Error {exc.response.status_code} from {exc.response.url}{detail}",
                err=True,
            )
            raise typer.Exit(1) from None

    # ------------------------------------------------------------------
    # Agent CRUD
    # ------------------------------------------------------------------

    def create(self, config: Path, ttl_seconds: int) -> None:
        """Deploy a new agent sandbox via multipart form upload.

        Args:
            config:      Path to the runner YAML configuration file.
            ttl_seconds: Sandbox time-to-live in seconds.
        """
        raw = yaml.safe_load(config.read_text()) or {}
        runner_cfg = RunnerConfig.from_dict(raw)  # validate structure; raises on bad fields
        name = runner_cfg.agent.name

        with config.open("rb") as fh:
            response = self._client.post(
                "/agents",
                data={"name": name, "ttl_seconds": str(ttl_seconds)},
                files={"config": (config.name, fh, "application/x-yaml")},
            )
        self._raise_for_status(response)
        data = response.json()
        status = data.get("status", "unknown")
        namespace = data.get("namespace", "unknown")
        typer.echo(f"Agent created: id={data['agent_id']}  namespace={namespace}  name={name}  status={status}")

    def list(self) -> None:
        """List all agents."""
        response = self._client.get("/agents")
        self._raise_for_status(response)
        agents = response.json()
        if not agents:
            typer.echo("No agents found.")
            return
        typer.echo(f"{'ID':<36}  {'NAMESPACE':<36}  STATUS")
        typer.echo("-" * 84)
        for agent in agents:
            typer.echo(f"{agent['agent_id']:<36}  {agent.get('namespace', ''):<36}  {agent.get('status', '')}")

    def delete(self, agent_id: str) -> None:
        """Delete an agent.

        Args:
            agent_id: The agent's unique identifier.
        """
        response = self._client.delete(f"/agents/{agent_id}")
        self._raise_for_status(response)
        typer.echo(f"Agent {agent_id} deleted.")

    def status(self, agent_id: str) -> None:
        """Show the health/status of a running agent.

        Args:
            agent_id: The agent's unique identifier.
        """
        response = self._client.get(f"/agents/{agent_id}/status")
        self._raise_for_status(response)
        data = response.json()
        state = data.get("status", "unknown")
        typer.echo(f"Agent {agent_id}  →  {state}")

    def card(self, agent_id: str) -> None:
        """Retrieve and display the A2A Agent Card for an agent.

        Args:
            agent_id: The agent's unique identifier.
        """
        response = self._client.get(f"/agents/{agent_id}/card")
        self._raise_for_status(response)
        data = response.json()
        typer.echo(f"Agent Card for {agent_id}:")
        typer.echo(f"  name        : {data.get('name', 'n/a')}")
        typer.echo(f"  description : {data.get('description', 'n/a')}")
        typer.echo(f"  version     : {data.get('version', 'n/a')}")
        typer.echo(f"  endpoint    : {data.get('endpoint', 'n/a')}")
        skills = data.get("skills", [])
        skill_ids = ", ".join(s.get("id", "") for s in skills) if skills else "none"
        typer.echo(f"  skills      : {skill_ids}")
        caps = data.get("capabilities", {})
        typer.echo(f"  streaming   : {caps.get('streaming', False)}")

    # ------------------------------------------------------------------
    # Runner-config template
    # ------------------------------------------------------------------

    def config_init(self, output: Path) -> None:
        """Write the default runner-config template to disk.

        Args:
            output: Destination file path (default: config.yaml).
        """
        write_default(output)
        typer.echo(f"Default config written to {output}")
        typer.echo("Edit the file before running `golem agent create`.")
