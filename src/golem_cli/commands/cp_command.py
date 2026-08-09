"""ControlPlane command — manage named control-plane endpoints."""

import httpx
import typer

from golem_cli import config as cfg
from golem_cli.config import ControlPlaneEntry

from .base import Command


class CpCommand(Command):
    """Encapsulates all control-plane management operations."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add(self, name: str, url: str) -> None:
        """Register a new control plane.

        Args:
            name: Unique alias for this control plane.
            url:  Base URL of the control plane (e.g. http://host:9000).
        """
        conf = cfg.load()
        if any(cp.name == name for cp in conf.control_planes):
            typer.echo(f"Control plane '{name}' already exists. Use `golem cp remove` first.", err=True)
            raise typer.Exit(1)
        conf.control_planes.append(ControlPlaneEntry(name=name, url=url.rstrip("/")))
        if not conf.active:
            conf.active = name
        cfg.save(conf)
        typer.echo(f"Control plane '{name}' registered at {url}.")
        if conf.active == name:
            typer.echo("  → Set as active.")

    def use(self, name: str) -> None:
        """Set the active control plane.

        Args:
            name: Alias of the control plane to activate.
        """
        conf = cfg.load()
        if not any(cp.name == name for cp in conf.control_planes):
            typer.echo(f"Control plane '{name}' not found. Run `golem cp list`.", err=True)
            raise typer.Exit(1)
        conf.active = name
        cfg.save(conf)
        typer.echo(f"Active control plane set to '{name}'.")

    def list(self) -> None:
        """List all registered control planes."""
        conf = cfg.load()
        if not conf.control_planes:
            typer.echo("No control planes registered. Run `golem cp add`.")
            return
        typer.echo(f"  {'NAME':<20}  {'URL':<40}  ACTIVE")
        typer.echo("  " + "-" * 68)
        for cp in conf.control_planes:
            marker = "✓" if cp.name == conf.active else ""
            typer.echo(f"  {cp.name:<20}  {cp.url:<40}  {marker}")

    def remove(self, name: str) -> None:
        """Remove a registered control plane.

        Args:
            name: Alias of the control plane to remove.
        """
        conf = cfg.load()
        before = len(conf.control_planes)
        conf.control_planes = [cp for cp in conf.control_planes if cp.name != name]
        if len(conf.control_planes) == before:
            typer.echo(f"Control plane '{name}' not found.", err=True)
            raise typer.Exit(1)
        if conf.active == name:
            conf.active = conf.control_planes[0].name if conf.control_planes else ""
        cfg.save(conf)
        typer.echo(f"Control plane '{name}' removed.")

    def status(self, name: str | None) -> None:
        """Check whether a control plane is healthy.

        Args:
            name: Alias to check; uses the active control plane when omitted.
        """
        conf = cfg.load()
        if name:
            matches = [cp for cp in conf.control_planes if cp.name == name]
            if not matches:
                typer.echo(f"Control plane '{name}' not found.", err=True)
                raise typer.Exit(1)
            url = matches[0].url
        else:
            url = cfg.get_active_url()
            name = conf.active
        try:
            response = httpx.get(f"{url}/health", timeout=5)
            response.raise_for_status()
            typer.echo(f"Control plane '{name}' ({url})  →  healthy ✓")
        except Exception as exc:
            typer.echo(f"Control plane '{name}' ({url})  →  unreachable ✗  ({exc})", err=True)
            raise typer.Exit(1) from None
