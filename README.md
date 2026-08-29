<p align="center">
  <img src="https://raw.githubusercontent.com/sasadangelo/golem-control-plane/main/docs/img/golem-logo.png" alt="Golem CLI" width="300" />
</p>

# Golem CLI

**Golem CLI** (`golem`) is the command-line client for the [Golem](https://github.com/sasadangelo/golem-control-plane) platform.

It communicates with the Golem Control Plane via REST (`httpx`) for agent lifecycle operations
and via WebSocket (`websockets`) for interactive streaming chat sessions.

> 📖 For the full platform overview, features, roadmap, and demos see the
> **[Golem Control Plane](https://github.com/sasadangelo/golem-control-plane)** repository.

---

## Installation

```bash
# 1. clone the repository
git clone https://github.com/sasadangelo/golem-cli.git
cd golem-cli

# 2. install dependencies and the golem entry point
uv sync
uv pip install -e .

# 3. install the golem binary into ~/.local/bin so it is available without 'uv run'
uv run pip install --target ~/.local/lib/golem .
ln -sf ~/.local/lib/golem/bin/golem ~/.local/bin/golem
# ensure ~/.local/bin is on your PATH (add to ~/.zshrc or ~/.bashrc if needed)
export PATH="$HOME/.local/bin:$PATH"

# verify
golem --help
```

---

## Getting Started

The CLI needs to know which Control Plane to talk to.
Register it once, then all commands resolve it automatically:

```bash
# point at a locally running Control Plane
golem cp add --name local --url http://localhost:9000
golem cp use --name local

# deploy an agent
golem agent create --config my-agent/config.yaml

# chat with it
golem chat --id my-agent-001
```

See **[docs/CommandReference.md](docs/CommandReference.md)** for the full command reference and usage examples.

---

## How the CLI is Configured

The CLI stores its state in `~/.golem/cli/config.yaml` — no environment variables required.

```yaml
active: "local"
control_planes:
  - name: "local"
    url:  "http://localhost:9000"
  - name: "prod"
    url:  "https://golem.example.com"
```

Use `golem cp` to manage this file:

```bash
golem cp add  --name prod --url https://golem.example.com
golem cp use  --name prod
golem cp list
golem cp remove --name local
golem cp status            # health-check the active control plane
```

If no active control plane is set, every command that requires the API fails immediately with a clear message.

---

## Command Reference

👉 **[docs/CommandReference.md](docs/CommandReference.md)** — full command table, options, and usage examples for every command group.

---

## Project Layout

```
golem-cli/
├── pyproject.toml                         # entry point: golem = "golem_cli.cli:main"
├── uv.lock                                # reproducible lockfile
├── docs/
│   ├── CommandReference.md                # full command table and usage examples
│   └── cli-design.md                      # design rationale, domain model, architecture
└── src/
    └── golem_cli/
        ├── cli.py                         # Typer wiring only — no business logic
        ├── config.py                      # ~/.golem/cli/config.yaml I/O
        ├── commands/
        │   ├── base.py                    # Command ABC
        │   ├── agent_command.py           # golem agent *
        │   ├── chat_command.py            # golem chat *
        │   ├── conversation_command.py    # golem conv *
        │   ├── cp_command.py              # golem cp *
        │   └── _agent_config_template.py  # default runner-config data + writer
        └── models/
            └── runner_config.py           # RunnerConfig Pydantic model
```

---

## Development

```bash
# install dev dependencies
uv sync --group dev

# lint + format
uv run ruff check . && uv run ruff format .

# type-check
uv run mypy src/

# tests
uv run pytest tests/

# pre-commit hooks
uv run pre-commit install
```

---

## License

MIT
