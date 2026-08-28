"""Default agent runner-config template data and writer.

Kept in a separate module to avoid bloating agent_command.py.
The template is a literal string so that quoted placeholders are preserved
exactly as written — yaml.dump strips quotes that are not syntactically needed.
"""

from pathlib import Path

_TEMPLATE = """\
agent:
  id: "<your-agent-id>"
  name: "<Your Agent Name>"
  description: "<Short description of what this agent does.>"
  endpoint: "http://localhost:8000"
  system_prompt: "<System prompt that defines the agent behaviour.>"
  enabled_skills: "bash,http_check"
  # cp_url: Control Plane base URL for handshake registration and A2A delegation.
  # Required only for agents that delegate tasks to other agents via the `delegate` skill.
  # Leave empty (or omit) for standalone agents.
  # Example:
  #   cp_url: "http://golem-cp.golem-system.svc.cluster.local:9000"
  #
  # delegation_timeout_seconds: max seconds to wait for a delegated A2A task to complete.
  # Only relevant for agents that use the `delegate` skill. Default: 300.
  # Example:
  #   delegation_timeout_seconds: 300
  #
  # mcp_servers: list of static MCP server URIs to connect at boot.
  # The runner calls MultiServerMCPClient with these URIs and registers each
  # server's tools into the LangGraph tool node automatically.
  # The MCP server must already be running and reachable from the pod.
  # Example (kubernetes-mcp-server deployed via Helm):
  #   mcp_servers:
  #     - "http://kubernetes-mcp-server.kubernetes-mcp-server.svc.cluster.local:8080"
  #
  # env_secrets: names of K8s Secrets already present in the agent namespace
  # to mount as envFrom in the pod. Create the secret before deploying:
  #   kubectl create secret generic my-credentials \
  #     --from-literal=MY_API_KEY=xxx -n <agent-id>
  # Example:
  #   env_secrets:
  #     - "my-credentials"
  #
  # triggers: background triggers that fire automatically without a user message.
  # Supported types: timer, cron, webhook.
  # Examples:
  #   triggers:
  #     - type: timer
  #       interval_seconds: 30
  #       message: "Check if http://my-service.svc.cluster.local/health is healthy."
  #     - type: cron
  #       cron: "0 9 * * 1-5"
  #       message: "Send the daily standup summary."
  #     - type: webhook
  #       path: "/trigger/my-event"
  #       message: "Handle incoming event."
llm:
  provider: "<llm-provider>"
  protocol: "<llm-protocol>"
  model: "<llm-model>"
  project_id: "<llm-project-id>"
  url: "<https://llm-api-url>"
log:
  level: INFO
  console: true
  file: logs/golem-runner.log
  rotation: 10 MB
  retention: 7 days
  compression: zip

# ---------------------------------------------------------------------------
# AGENT IDENTITY & SKILLS (Week 4)
#
# Supply these as separate file uploads when running `golem agent create`:
#
#   golem agent create \
#     --config config.yaml \
#     --agents-md AGENTS.md \
#     --skill read-logs.md \
#     --skill summarize.md
#
# AGENTS.md  — mounted at /app/AGENTS.md; defines who the agent is and how
#              it should behave (personality, tone, constraints).
#
# SKILL.md   — one file per skill; mounted at /app/skills/<name>.md; injected
#              into the system message lazily (per turn) when the user's
#              message matches the skill name.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# LOCAL SMOKE-TEST ONLY — never uncomment in production.
#
# Overrides used to run the full client → Control Plane → Runner flow on a
# local workstation without Docker or Kubernetes.
#
# Steps:
#   1. Start the runner:  cd <golem-runner>/src/golem-runner
#                         uv run uvicorn main:app --port 8000
#   2. Uncomment the block below.
#   3. Start the Control Plane: uv run uvicorn interfaces.api.app:app --port 9000
#   4. Create a sandbox via POST /agents.
#   5. Chat: wscat -c ws://localhost:9000/chat/<agent_id>
# ---------------------------------------------------------------------------
# test:
#   provisioner: "mock"
#   runner_url: "ws://localhost:8000/ws/chat"
"""


def write_default(output: Path) -> None:
    """Write the default RunnerConfig template to *output*."""
    output.write_text(_TEMPLATE)
