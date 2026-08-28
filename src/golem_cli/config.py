"""golem CLI — persistent configuration.

The CLI home directory is resolved from the ``GOLEM_PATH`` environment variable,
defaulting to ``~/.golem``.  The config file is always at::

    $GOLEM_PATH/cli/config.yaml

Schema:
    active: "<name>"          # name of the currently active control plane
    control_planes:
      - name: "local"
        url:  "http://localhost:9000"
    active_conversations:     # active conversation per agent
      "<agent_id>": "<conversation_id>"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import typer
import yaml

# Base directory: honour GOLEM_PATH env var, fall back to ~/.golem
GOLEM_PATH = Path(os.environ.get("GOLEM_PATH", str(Path.home() / ".golem")))
CONFIG_PATH = GOLEM_PATH / "cli" / "config.yaml"


@dataclass
class ControlPlaneEntry:
    """A named control-plane endpoint."""

    name: str
    url: str


@dataclass
class GolemConfig:
    """Top-level golem CLI configuration."""

    active: str = ""
    control_planes: list[ControlPlaneEntry] = field(default_factory=list)
    # Maps agent_id → conversation_id for the currently active conversation.
    active_conversations: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load() -> GolemConfig:
    """Read config from disk.  Returns empty defaults when the file is absent."""
    if not CONFIG_PATH.exists():
        return GolemConfig()
    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    cps = [ControlPlaneEntry(name=cp["name"], url=cp["url"]) for cp in raw.get("control_planes", [])]
    active_conversations: dict[str, str] = raw.get("active_conversations") or {}
    return GolemConfig(
        active=raw.get("active", ""),
        control_planes=cps,
        active_conversations=active_conversations,
    )


def save(cfg: GolemConfig) -> None:
    """Write config to disk, creating parent directories as needed."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "active": cfg.active,
        "control_planes": [{"name": cp.name, "url": cp.url} for cp in cfg.control_planes],
        "active_conversations": cfg.active_conversations,
    }
    CONFIG_PATH.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ---------------------------------------------------------------------------
# Active control-plane resolution
# ---------------------------------------------------------------------------


def get_active_url() -> str:
    """Return the URL of the active control plane.

    Raises:
        typer.Exit: with a clear message when no active control plane is set.
    """
    cfg = load()
    if not cfg.active:
        typer.echo(
            "No active control plane. Run `golem cp use --name <name>` to select one, "
            "or `golem cp add` to register a new one.",
            err=True,
        )
        raise typer.Exit(1)
    for cp in cfg.control_planes:
        if cp.name == cfg.active:
            return cp.url
    typer.echo(
        f"Active control plane '{cfg.active}' not found in config. "
        "Run `golem cp list` to see available control planes.",
        err=True,
    )
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Active conversation resolution
# ---------------------------------------------------------------------------


def get_active_conversation(agent_id: str) -> str | None:
    """Return the active conversation_id for ``agent_id``, or None if not set."""
    return load().active_conversations.get(agent_id)


def set_active_conversation(agent_id: str, conversation_id: str) -> None:
    """Persist ``conversation_id`` as the active conversation for ``agent_id``."""
    cfg = load()
    cfg.active_conversations[agent_id] = conversation_id
    save(cfg)


def clear_active_conversation(agent_id: str) -> None:
    """Remove the active conversation for ``agent_id`` if one is set."""
    cfg = load()
    cfg.active_conversations.pop(agent_id, None)
    save(cfg)
