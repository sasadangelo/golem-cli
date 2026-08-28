"""Conversation command — manage isolated conversations for an agent."""

import httpx
import typer

from golem_cli import config as cfg

from .base import Command


class ConversationCommand(Command):
    """Encapsulates all conversation lifecycle operations."""

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
    # Conversation CRUD
    # ------------------------------------------------------------------

    def list(self, agent_id: str) -> None:
        """List all conversations for an agent.

        Args:
            agent_id: The agent's unique identifier.
        """
        response = self._client.get(f"/agents/{agent_id}/conversations")
        self._raise_for_status(response)
        conversations = response.json()
        if not conversations:
            typer.echo(f"No conversations found for agent {agent_id}.")
            return
        typer.echo(f"{'ID':<38}  {'NAME':<24}  ACTIVE")
        typer.echo("-" * 70)
        for conv in conversations:
            marker = "✓" if conv.get("is_active", False) else ""
            name = conv.get("name") or ""
            typer.echo(f"{conv['conversation_id']:<38}  {name:<24}  {marker}")

    def new(self, agent_id: str, name: str = "") -> None:
        """Create a new conversation and make it active.

        Args:
            agent_id: The agent's unique identifier.
            name:     Optional human-readable label.
        """
        response = self._client.post(f"/agents/{agent_id}/conversations", json={"name": name})
        self._raise_for_status(response)
        data = response.json()
        conv_id: str = data["conversation_id"]
        cfg.set_active_conversation(agent_id, conv_id)
        label = f"  name={data.get('name')!r}" if data.get("name") else ""
        typer.echo(f"Conversation created: id={conv_id}{label}")
        typer.echo(f"  → Set as active conversation for agent {agent_id}.")

    def delete(self, agent_id: str, conversation_id: str, force: bool = False) -> None:
        """Delete a conversation.

        Args:
            agent_id:        The agent's unique identifier.
            conversation_id: The conversation UUID to delete.
            force:           Force deletion even if active connections exist.
        """
        url = f"/agents/{agent_id}/conversations/{conversation_id}"
        if force:
            url += "?force=true"
        response = self._client.delete(url)
        self._raise_for_status(response)
        typer.echo(f"Conversation {conversation_id} deleted successfully.")
