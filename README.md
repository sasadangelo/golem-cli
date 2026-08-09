# Golem CLI

Command-line client for the **Golem Agent-as-a-Service** platform.

`golem` communicates with the Golem Control Plane via REST (`httpx`) for
agent lifecycle operations and via WebSocket (`websockets`) for interactive
chat sessions.

---

## Features

| Feature | Status |
|---|:---:|
| Multi-context control plane management (`golem cp add/use/list/remove/status`) | ✅ |
| Agent sandbox lifecycle — create, list, delete, status (`golem agent create/list/delete/status`) | ✅ |
| Runner config template generator (`golem agent config --generate`) | ✅ |
| Interactive WebSocket chat with an agent, with token streaming (`golem chat --id <id>`) | ✅ |
| Persistent CLI config in `~/.golem/cli/config.yaml` (multi-context, survives restarts) | ✅ |
| `golem conv` — multi-conversation management (list, new, switch, delete) | 🔜 |
| `golem agent tasks` — A2A task lifecycle view | 🔜 |

---


## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/sasadangelo/golem-cli.git
cd golem-cli
```

### 2. Install the project in editable mode

```bash
uv sync
uv pip install -e .
```

The `golem` binary is now available in your virtualenv.

### 3. Activate the virtualenv (optional — or prefix commands with `uv run`)

```bash
source .venv/bin/activate
# or, without activation:
uv run golem --help
```

---

## Configuration

The CLI reads the Control Plane URL from an environment variable:

| Variable                  | Default                   | Description                    |
|---------------------------|---------------------------|--------------------------------|
| `GOLEM_CONTROL_PLANE_URL` | `http://localhost:9000`   | Base URL of the Control Plane  |

```bash
export GOLEM_CONTROL_PLANE_URL=http://my-control-plane:9000
```

---

## Usage

### Agent commands

```bash
# Generate a default config template, then customise it
golem agent config init
golem agent config init --output my-agent.yaml

# Deploy a new agent sandbox
golem agent create --name "my-agent" --config config.yaml

# List all agents
golem agent list

# Show details of a specific agent
golem agent show --id <agent-id>

# Delete an agent
golem agent delete --id <agent-id>
```

### Chat commands

```bash
# Start a new interactive chat session with an agent
golem chat new --agent <agent-id>

# Resume an existing conversation
golem chat switch --agent <agent-id> --id <chat-id>

# List all conversations for an agent
golem chat list --agent <agent-id>

# Delete a conversation
golem chat delete --id <chat-id>
```

### Help

Every command and subcommand supports `--help`:

```bash
golem --help
golem agent --help
golem agent config --help
golem chat --help
```

---

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run linter + formatter
uv run ruff check . && uv run ruff format .

# Type-check
uv run mypy src/

# Run tests
uv run pytest tests/
```

### Pre-commit hooks

```bash
uv run pre-commit install
```

---

## Project structure

```
golem-cli/
├── pyproject.toml              ← entry point, dependencies, tool config
├── README.md
├── docs/
│   └── cli-design.md           ← domain model, command design, architecture
└── src/
    └── golem_cli/
        ├── __init__.py
        ├── cli.py              ← Typer wiring only (no business logic)
        └── commands/
            ├── __init__.py
            ├── base.py         ← Marker ABC
            ├── agent_command.py
            └── chat_command.py
```

See [`docs/cli-design.md`](docs/cli-design.md) for the full design rationale,
domain diagram, command table, and architecture overview.
