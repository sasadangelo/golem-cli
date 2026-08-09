from abc import ABC


class Command(ABC):  # noqa: B024
    """Marker base class for CLI commands.

    Typer handles argument parsing and command dispatch.
    Each subclass defines its own typed method signatures.
    """
