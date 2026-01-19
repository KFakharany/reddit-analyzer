"""Base agent class for Claude SDK integration."""

import json
from dataclasses import dataclass
from typing import Any, Optional

from anthropic import Anthropic

from src.config import get_settings, get_model_for_task
from src.config.agent_configs import AgentConfig, AGENT_CONFIGS


@dataclass
class AgentResponse:
    """Response from an agent."""

    content: str
    parsed: Optional[dict[str, Any]] = None
    model: str = ""
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None


class BaseAgent:
    """Base class for Claude SDK agents."""

    def __init__(
        self,
        config_name: str,
        config_override: Optional[AgentConfig] = None,
    ):
        """Initialize the agent.

        Args:
            config_name: Name of the agent configuration to use.
            config_override: Optional override configuration.
        """
        self.config_name = config_name
        self.config = config_override or AGENT_CONFIGS.get(config_name)

        if not self.config:
            raise ValueError(f"Unknown agent configuration: {config_name}")

        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = get_model_for_task(self.config.model_key)

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create the user prompt from data.

        Override this in subclasses for custom prompt formatting.

        Args:
            data: Data to include in the prompt.

        Returns:
            Formatted prompt string.
        """
        return json.dumps(data, indent=2, default=str)

    def _parse_response(self, content: str) -> Optional[dict[str, Any]]:
        """Parse the agent's response as JSON.

        Args:
            content: Raw response content.

        Returns:
            Parsed JSON or None if parsing fails.
        """
        # Try to extract JSON from the response
        content = content.strip()

        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            return None

    def run(self, data: dict[str, Any]) -> AgentResponse:
        """Run the agent with the given data.

        Args:
            data: Data to analyze.

        Returns:
            AgentResponse with results.
        """
        try:
            prompt = self._create_prompt(data)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.config.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            parsed = self._parse_response(content)

            return AgentResponse(
                content=content,
                parsed=parsed,
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                success=True,
            )

        except Exception as e:
            return AgentResponse(
                content="",
                parsed=None,
                model=self.model,
                success=False,
                error=str(e),
            )

    async def run_async(self, data: dict[str, Any]) -> AgentResponse:
        """Async version of run (uses sync client internally).

        Args:
            data: Data to analyze.

        Returns:
            AgentResponse with results.
        """
        # For now, just wrap the sync method
        # Can be updated to use async client if needed
        return self.run(data)
