# Golem CLI — Command Reference

Full command table, options, and usage examples for every `golem` command group.

---

## `golem cp` — Control Plane Management

These commands do **not** require an active control plane.

| Subcommand | Options | Description |
|---|---|---|
| `cp add` | `--name/-n` (req), `--url/-u` (req) | Register a new control plane endpoint |
| `cp use` | `--name/-n` (req) | Set the active control plane |
| `cp list` | — | List all registered control planes |
| `cp remove` | `--name/-n` (req) | Remove a registered control plane |
| `cp status` | `--name/-n` (optional, default: active) | Health-check a control plane |

```bash
golem cp add    --name local --url http://localhost:9000
golem cp add    --name prod  --url https://golem.example.com
golem cp use    --name prod
golem cp list
golem cp status
golem cp status --name local
golem cp remove --name local
```

---

## `golem agent` — Agent Sandbox Lifecycle

All `agent` subcommands require an active control plane (`golem cp use`).

| Subcommand | Options | Description |
|---|---|---|
| `agent create` | `--config/-c` (path, req), `--agents-md` (path, opt), `--skill/-s` (path, repeatable), `--ttl/-t` (int, opt) | Deploy a new agent sandbox |
| `agent list` | — | List all agents |
| `agent show` | `--id/-i` (str, req) | Show details of one agent |
| `agent delete` | `--id/-i` (str, req) | Delete an agent |
| `agent status` | `--id/-i` (str, req) | Show health/readiness of a running agent |

```bash
# generate a runner config template, then customise it
golem agent config init
golem agent config init --output my-agent.yaml

# create a persistent agent (no TTL — lives until deleted)
golem agent create --config my-agent.yaml

# create an agent with AGENTS.md and skills
golem agent create \
  --config       examples/demo-sre/agent/config.yaml \
  --agents-md    examples/demo-sre/agent/AGENTS.md \
  --skill        examples/demo-sre/agent/skills/check-health.md \
  --skill        examples/demo-sre/agent/skills/inspect-env.md

# create an ephemeral agent (auto-deleted after 1 hour)
golem agent create --config my-agent.yaml --ttl 3600

# lifecycle
golem agent list
golem agent show   --id my-agent-001
golem agent status --id my-agent-001
golem agent delete --id my-agent-001
```

---

## `golem chat` — Interactive Chat

`golem chat` opens a streaming WebSocket session with an agent.

| Subcommand / Option | Description |
|---|---|
| `golem chat --id <agent-id>` | Open a new chat session (new conversation) |
| `golem chat --id <agent-id> --conv <conv-id>` | Resume an existing conversation |

```bash
# start a new chat with an agent
golem chat --id my-agent-001

# resume a specific conversation
golem chat --id my-agent-001 --conv conv-abc123
```

Tokens are streamed to the terminal as they arrive. The session terminates on `[DONE]`.

---

## `golem conv` — Conversation Management

| Subcommand | Options | Description |
|---|---|---|
| `conv list` | `--agent/-a` (str, req) | List all conversations for an agent |
| `conv new` | `--agent/-a` (str, req), `--name` (str, opt) | Create a new conversation |
| `conv delete` | `--id/-i` (str, req) | Delete a conversation |

```bash
golem conv list   --agent my-agent-001
golem conv new    --agent my-agent-001 --name "Security review session"
golem conv delete --id conv-abc123
```

---

## `golem agent tasks` — A2A Task Lifecycle

| Subcommand | Options | Description |
|---|---|---|
| `agent tasks` | `--agent/-a` (str, req) | List all A2A tasks for an agent |
| `agent task-send` | `--agent/-a` (str, req), `--message/-m` (str, req), `--wait` (flag), `--timeout` (int, default 300) | Submit an A2A task |
| `agent task-get` | `--agent/-a` (str, req), `--task/-t` (str, req) | Get the result of a specific task |

```bash
# submit a task and return immediately (non-blocking)
golem agent task-send --agent log-analyzer-001 \
  --message "Analyse the application logs and produce a formal incident report."

# submit and block until the task completes (max 5 minutes)
golem agent task-send --agent log-analyzer-001 \
  --message "Analyse the application logs and produce a formal incident report." \
  --wait --timeout 300

# list all tasks for an agent
golem agent tasks --agent log-analyzer-001

# read the result of a specific task
golem agent task-get --agent log-analyzer-001 --task task-abc123
```

---

## Getting Help

Every command and subcommand supports `--help`:

```bash
golem --help
golem agent --help
golem agent create --help
golem chat --help
golem conv --help
```
