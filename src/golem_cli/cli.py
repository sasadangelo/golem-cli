"""golem CLI — Typer wiring only. No business logic lives here."""

from pathlib import Path

import typer

from golem_cli.commands.agent_command import AgentCommand
from golem_cli.commands.chat_command import ChatCommand
from golem_cli.commands.cp_command import CpCommand

app = typer.Typer(
    name="golem",
    help="golem — Golem Agent-as-a-Service CLI",
    no_args_is_help=True,
    add_completion=False,
)

# ---------------------------------------------------------------------------
# cp sub-app  (control-plane management — no active CP required)
# ---------------------------------------------------------------------------
cp_app = typer.Typer(help="Manage control-plane endpoints.", no_args_is_help=True)
app.add_typer(cp_app, name="cp")

# ---------------------------------------------------------------------------
# agent sub-app
# ---------------------------------------------------------------------------
agent_app = typer.Typer(help="Manage agent sandboxes.", no_args_is_help=True)
app.add_typer(agent_app, name="agent")

# ---------------------------------------------------------------------------
# cp commands  (instantiated at module level — no active CP needed)
# ---------------------------------------------------------------------------
_cp = CpCommand()


@cp_app.command("add")
def cp_add(
    name: str = typer.Option(..., "--name", "-n", help="Unique alias for this control plane."),  # noqa: B008
    url: str = typer.Option(..., "--url", "-u", help="Base URL (e.g. http://host:9000)."),  # noqa: B008
) -> None:
    """Register a new control-plane endpoint."""
    _cp.add(name=name, url=url)


@cp_app.command("use")
def cp_use(
    name: str = typer.Option(..., "--name", "-n", help="Alias of the control plane to activate."),  # noqa: B008
) -> None:
    """Set the active control plane."""
    _cp.use(name=name)


@cp_app.command("list")
def cp_list() -> None:
    """List all registered control planes."""
    _cp.list()


@cp_app.command("remove")
def cp_remove(
    name: str = typer.Option(..., "--name", "-n", help="Alias of the control plane to remove."),  # noqa: B008
) -> None:
    """Remove a registered control plane."""
    _cp.remove(name=name)


@cp_app.command("status")
def cp_status(
    name: str | None = typer.Option(None, "--name", "-n", help="Alias to check (defaults to active)."),  # noqa: B008
) -> None:
    """Check whether a control plane is healthy."""
    _cp.status(name=name)


# ---------------------------------------------------------------------------
# agent commands  (instantiated lazily — require an active CP)
# ---------------------------------------------------------------------------


@agent_app.command("create")
def agent_create(
    config: Path = typer.Option(..., "--config", "-c", help="Path to the runner config YAML."),  # noqa: B008
    ttl: int = typer.Option(3600, "--ttl", "-t", help="Sandbox time-to-live in seconds."),  # noqa: B008
) -> None:
    """Deploy a new agent sandbox."""
    AgentCommand().create(config=config, ttl_seconds=ttl)


@agent_app.command("list")
def agent_list() -> None:
    """List all agents."""
    AgentCommand().list()


@agent_app.command("delete")
def agent_delete(
    agent_id: str = typer.Option(..., "--id", "-i", help="Agent ID."),  # noqa: B008
) -> None:
    """Delete an agent."""
    AgentCommand().delete(agent_id=agent_id)


@agent_app.command("status")
def agent_status(
    agent_id: str = typer.Option(..., "--id", "-i", help="Agent ID."),  # noqa: B008
) -> None:
    """Show the health status of a running agent."""
    AgentCommand().status(agent_id=agent_id)


@agent_app.command("card")
def agent_card(
    agent_id: str = typer.Option(..., "--id", "-i", help="Agent ID."),  # noqa: B008
) -> None:
    """Display the A2A Agent Card for an agent (skills, capabilities, endpoint)."""
    AgentCommand().card(agent_id=agent_id)


# ---------------------------------------------------------------------------
# agent config command  (no active CP needed — writes a local file)
# ---------------------------------------------------------------------------


@agent_app.command("config")
def agent_config(
    generate: bool = typer.Option(False, "--generate", "-g", help="Generate a default runner-config template."),  # noqa: B008
    output: Path = typer.Option(Path("config.yaml"), "--output", "-o", help="Destination file path."),  # noqa: B008
) -> None:
    """Manage the agent runner-config template."""
    if not generate:
        typer.echo("Use --generate to create a default runner-config template.", err=True)
        raise typer.Exit(1)
    from golem_cli.commands._agent_config_template import write_default  # local import — no CP needed

    write_default(output)
    typer.echo(f"Default config written to {output}")
    typer.echo("Edit the file before running `golem agent create`.")


# ---------------------------------------------------------------------------
# chat command  (stateless WebSocket session — no server-side chat management)
# ---------------------------------------------------------------------------


@app.command("chat")
def chat(
    agent_id: str = typer.Option(..., "--id", "-i", help="Agent ID to chat with."),  # noqa: B008
) -> None:
    """Open an interactive chat session with an agent."""
    ChatCommand().connect(agent_id=agent_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    app()
