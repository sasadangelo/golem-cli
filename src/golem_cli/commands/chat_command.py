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
        base_url = cfg.get_active_url()
        self._ws_base = base_url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")

    def connect(self, agent_id: str) -> None:
        """Open an interactive WebSocket chat session with an agent.

        Args:
            agent_id: The agent to chat with.
        """
        uri = f"{self._ws_base}/chat/{agent_id}"
        typer.echo(f"Connecting to {uri}  (type 'exit' or Ctrl-C to quit)\n")
        asyncio.run(self._ws_repl(uri))

    @staticmethod
    async def _ws_repl(uri: str) -> None:
        async with websockets.connect(uri) as ws:
            try:
                while True:
                    typer.echo("you> ", nl=False)
                    user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    user_input = user_input.rstrip("\n")
                    if user_input.lower() in {"exit", "quit"}:
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
                typer.echo("\nConnection closed by server.")
            except KeyboardInterrupt:
                typer.echo("\nSession ended.")
