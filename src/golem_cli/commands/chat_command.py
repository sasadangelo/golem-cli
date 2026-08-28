"""Chat command — stateless WebSocket session with an agent runner."""

import asyncio
import sys

import typer
import websockets
from websockets.exceptions import ConnectionClosedOK

from golem_cli import config as cfg

from .base import Command


class ChatCommand(Command):
    """Encapsulates the interactive WebSocket chat session."""

    def __init__(self) -> None:
        self._base_url = cfg.get_active_url()
        self._ws_base = self._base_url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")

    def connect(self, agent_id: str, conversation_id: str | None = None, name: str | None = None) -> None:
        """Open an interactive WebSocket chat session with an agent.

        When ``conversation_id`` is provided, the session resumes that conversation's
        isolated history on the runner.  Otherwise, a new conversation is automatically
        created on the Control Plane.

        Args:
            agent_id:        The agent to chat with.
            conversation_id: Optional explicit conversation UUID to resume.
            name:            Optional human-readable label for a new conversation.
        """
        resolved_conv_id = None

        if conversation_id:
            resolved_conv_id = conversation_id
            typer.echo(f"Resuming conversation {resolved_conv_id}")

        # If no conversation_id was specified (default run), automatically create a new conversation
        # via POST on the Control Plane.
        if not resolved_conv_id:
            import httpx

            try:
                with httpx.Client(base_url=self._base_url, timeout=10) as client:
                    response = client.post(f"/agents/{agent_id}/conversations", json={"name": name or ""})
                    response.raise_for_status()
                    data = response.json()
                    resolved_conv_id = data["conversation_id"]
                    if name:
                        typer.echo(f"Created new conversation {name!r}: {resolved_conv_id}")
                    else:
                        typer.echo(f"Created new conversation: {resolved_conv_id}")
            except Exception as exc:
                typer.echo(
                    f"Warning: Failed to auto-create conversation ({exc}). Falling back to stateless chat.", err=True
                )

        if resolved_conv_id:
            uri = f"{self._ws_base}/chat/{agent_id}?conversation_id={resolved_conv_id}"
        else:
            uri = f"{self._ws_base}/chat/{agent_id}"

        typer.echo(f"Connecting to {uri}  (type 'exit' or Ctrl-C to quit)\n")
        asyncio.run(self._ws_repl(uri))

    @staticmethod
    async def _ws_repl(uri: str) -> None:
        async with websockets.connect(uri) as ws:
            clean_exit = False

            async def monitor_closure() -> None:
                try:
                    await ws.wait_closed()
                    if not clean_exit:
                        typer.echo("\nConnection closed by server.")
                        import os

                        os._exit(0)
                except Exception:  # nosec B110 - intentionally ignore errors on ws close
                    pass

            monitor_task = asyncio.create_task(monitor_closure())

            try:
                while True:
                    typer.echo("you> ", nl=False)
                    user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    user_input = user_input.rstrip("\n")
                    if user_input.lower() in {"exit", "quit"}:
                        clean_exit = True
                        break
                    await ws.send(user_input)
                    typer.echo("agent> ", nl=False)
                    while True:
                        frame = await ws.recv()
                        text = frame if isinstance(frame, str) else frame.decode()
                        if text == "[DONE]":
                            typer.echo("")
                            break
                        if text.startswith("[ERROR]"):
                            typer.echo(text)
                            break
                        typer.echo(text, nl=False)
            except ConnectionClosedOK:
                if not clean_exit:
                    typer.echo("\nConnection closed by server.")
            except KeyboardInterrupt:
                typer.echo("\nSession ended.")
            finally:
                clean_exit = True
                monitor_task.cancel()
