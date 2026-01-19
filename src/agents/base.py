"""
Base agent wrapper for Claude Agent SDK calls.

Standardizes how all agents call the SDK, handles error catching,
and ensures consistent output format.

The Claude Agent SDK uses the CLI's existing authentication (OAuth or stored credentials),
so no API key is needed in code.
"""

import asyncio
import time
import json
from dataclasses import dataclass
from typing import Any, Optional

from src.config import get_model_for_task
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
    execution_time_ms: int = 0


class BaseAgent:
    """Base class for Claude Agent SDK agents."""

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
        if not content:
            return None

        # Try direct JSON parse
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass

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
        # Run the async version synchronously
        return asyncio.run(self.run_async(data))

    async def run_async(self, data: dict[str, Any]) -> AgentResponse:
        """Async version of run using Claude Agent SDK.

        Args:
            data: Data to analyze.

        Returns:
            AgentResponse with results.
        """
        start_time = time.time()

        try:
            # Import SDK here to avoid import errors if not installed
            from claude_agent_sdk import (
                query,
                ClaudeAgentOptions,
                AssistantMessage,
                ResultMessage,
                TextBlock,
            )

            prompt = self._create_prompt(data)

            # Build the full prompt with system context
            full_prompt = f"""System: {self.config.system_prompt}

User: {prompt}

Please respond with valid JSON only."""

            # Configure the agent options
            options = ClaudeAgentOptions(
                model=self.model,
                allowed_tools=[],  # No tools needed for analysis
                permission_mode="bypassPermissions",
                cwd="/tmp",
            )

            output_text = ""

            async def execute():
                nonlocal output_text
                async for message in query(prompt=full_prompt, options=options):
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                output_text += block.text
                    elif isinstance(message, ResultMessage):
                        if message.is_error:
                            raise Exception(f"Agent returned error: {message.result}")
                        if message.result and not output_text:
                            output_text = message.result

            await asyncio.wait_for(execute(), timeout=60)

            execution_time_ms = int((time.time() - start_time) * 1000)
            parsed = self._parse_response(output_text)

            return AgentResponse(
                content=output_text,
                parsed=parsed,
                model=self.model,
                tokens_used=0,
                success=True,
                execution_time_ms=execution_time_ms,
            )

        except asyncio.TimeoutError:
            return AgentResponse(
                content="",
                parsed=None,
                model=self.model,
                success=False,
                error="Agent timed out after 60s",
                execution_time_ms=60000,
            )

        except ImportError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                content="",
                parsed=None,
                model=self.model,
                success=False,
                error=f"Claude Agent SDK not installed. Install with: pip install claude-agent-sdk. Error: {str(e)}",
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                content="",
                parsed=None,
                model=self.model,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
