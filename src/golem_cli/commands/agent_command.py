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

    def create(
        self,
        config: Path,
        ttl_seconds: int,
        agents_md: Path | None = None,
        skills: list[Path] | None = None,
    ) -> None:
        """Deploy a new agent sandbox via multipart form upload.

        Args:
            config:      Path to the runner YAML configuration file.
            ttl_seconds: Sandbox time-to-live in seconds.
            agents_md:   Optional path to an AGENTS.md file mounted at /app/AGENTS.md.
            skills:      Optional list of SKILL.md file paths; each is mounted at
                         /app/skills/<stem>.md inside the pod.
        """
        raw = yaml.safe_load(config.read_text()) or {}
        runner_cfg = RunnerConfig.from_dict(raw)  # validate structure; raises on bad fields
        name = runner_cfg.agent.name

        files: list[tuple[str, tuple]] = []
        # config is always present
        files.append(("config", (config.name, config.open("rb"), "application/x-yaml")))

        if agents_md is not None:
            files.append(("agents_md", (agents_md.name, agents_md.open("rb"), "text/markdown")))

        for skill_path in skills or []:
            files.append(("skills", (skill_path.name, skill_path.open("rb"), "text/markdown")))

        response = self._client.post(
            "/agents",
            data={"name": name, "ttl_seconds": str(ttl_seconds)},
            files=files,
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
    # A2A task lifecycle
    # ------------------------------------------------------------------

    def task_send(self, agent_id: str, message: str, wait: bool = False, timeout: int = 30) -> None:
        """Submit a one-shot A2A task to an agent (fire-and-forget by default).

        Calls POST /agents/{agent_id}/tasks on the Control Plane.  By default
        returns immediately with the task_id.  Pass wait=True to poll until
        completion or the timeout is reached.

        Args:
            agent_id: The agent's unique identifier.
            message:  The instruction text to send to the agent.
            wait:     If True, poll until the task reaches a terminal state.
            timeout:  Max seconds to wait when wait=True (default 30).
        """
        response = self._client.post(
            f"/agents/{agent_id}/tasks",
            json={"message": message, "source": "golem-cli"},
        )
        self._raise_for_status(response)
        data = response.json()
        task_id = data.get("task_id", "")
        status = data.get("status", "submitted")
        typer.echo(f"Task submitted: id={task_id}  status={status}")

        if not wait:
            typer.echo(f"Poll result with: golem agent task-get --agent {agent_id} --task {task_id}")
            return

        import time

        typer.echo(f"Waiting for completion (timeout={timeout}s) ...")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(3)
            poll = self._client.get(f"/agents/{agent_id}/tasks/{task_id}")
            if poll.status_code != 200:
                continue
            t = poll.json()
            st = t.get("status", "")
            if st == "completed":
                typer.echo(f"Status: {st}")
                if t.get("result"):
                    typer.echo(f"\n{t['result']}")
                return
            if st == "failed":
                typer.echo(f"Status: {st}")
                if t.get("result"):
                    typer.echo(f"\n{t['result']}")
                raise typer.Exit(1)
            typer.echo(f"  status={st} ...")
        typer.echo(f"Timed out after {timeout}s — task {task_id} still running.", err=True)
        raise typer.Exit(1)

    def task_get(self, agent_id: str, task_id: str) -> None:
        """Show details of a single A2A task.

        Args:
            agent_id: The agent's unique identifier.
            task_id:  The task's unique identifier.
        """
        response = self._client.get(f"/agents/{agent_id}/tasks/{task_id}")
        self._raise_for_status(response)
        data = response.json()
        typer.echo(f"Task {task_id}  agent={agent_id}  status={data.get('status', 'unknown')}")
        if data.get("result"):
            typer.echo(f"\n{data['result']}")

    def tasks(self, agent_id: str) -> None:
        """Show the A2A task lifecycle for an agent.

        Queries GET /agents/{agent_id}/tasks on the Control Plane and prints
        each task with its ID, status, and a short message excerpt.

        Args:
            agent_id: The agent's unique identifier.
        """
        response = self._client.get(f"/agents/{agent_id}/tasks")
        self._raise_for_status(response)
        items = response.json()
        if not items:
            typer.echo(f"No tasks found for agent {agent_id}.")
            return
        typer.echo(f"{'TASK ID':<28}  {'SOURCE':<10}  {'STATUS':<12}  {'UPDATED AT':<21}  MESSAGE")
        typer.echo("-" * 108)
        for task in items:
            task_id = task.get("task_id", "")
            source = task.get("source", "manual")
            status = task.get("status", "")
            updated_at = task.get("updated_at", "")[:19].replace("T", " ")
            message = task.get("message", "")
            msg_short = message[:48] + "…" if len(message) > 48 else message
            typer.echo(f"{task_id:<28}  {source:<10}  {status:<12}  {updated_at:<21}  {msg_short}")

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
