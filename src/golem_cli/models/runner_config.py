"""Runner configuration model.

RunnerConfig is the full YAML structure uploaded when deploying an agent sandbox.
It is the single source of truth for all runner config fields and defaults.
"""

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Identity and behaviour settings for an agent runner sandbox."""

    id: str = "<your-agent-id>"
    name: str = "<Your Agent Name>"
    description: str = "<Short description of what this agent does.>"
    endpoint: str = "http://localhost:8000"
    system_prompt: str = "<System prompt that defines the agent behaviour.>"
    enabled_skills: str = "bash,http_check"


@dataclass
class LLMConfig:
    """LLM provider settings."""

    provider: str = "<llm-provider>"
    protocol: str = "<llm-protocol>"
    model: str = "<llm-model>"
    project_id: str = "<llm-project-id>"
    url: str = "<https://llm-api-url>"


@dataclass
class LogConfig:
    """Logging settings."""

    level: str = "INFO"
    console: bool = True
    file: str = "logs/golem-control-plane.log"
    rotation: str = "10 MB"
    retention: str = "7 days"
    compression: str = "zip"


@dataclass
class RunnerConfig:
    """Full configuration for an agent runner sandbox.

    Serialised to YAML and uploaded as a multipart field on ``agent create``.
    Generate a default template with ``golem agent config init``.
    """

    agent: AgentConfig = field(default_factory=AgentConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    log: LogConfig = field(default_factory=LogConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "RunnerConfig":
        """Parse a raw YAML dict into a RunnerConfig.

        Args:
            data: Dict loaded from the runner config YAML file.

        Returns:
            A populated RunnerConfig instance.
        """
        agent = data.get("agent", {})
        llm = data.get("llm", {})
        log = data.get("log", {})
        return cls(
            agent=AgentConfig(**{k.replace("-", "_"): v for k, v in agent.items()}),
            llm=LLMConfig(**llm),
            log=LogConfig(**log),
        )
