"""MCP Prompts for {{AGENT_NAME}} agent.

This is where you implement your agent's prompts (templates).
Prompts provide pre-defined templates that help users interact
with your agent more effectively.

Example prompts are provided below - replace them with your own.
"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Prompt, PromptMessage, TextContent, PromptArgument

logger = logging.getLogger(__name__)


def register(server: Server):
    """Register prompts with the MCP server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """Return list of available prompts."""
        return [
            Prompt(
                name="diagnostic_analysis",
                description="Template for diagnostic analysis of a target",
                arguments=[
                    PromptArgument(
                        name="target_id",
                        description="ID of the target to analyze",
                        required=True
                    ),
                    PromptArgument(
                        name="problem_description",
                        description="Description of the problem",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="health_report",
                description="Template for generating a health report",
                arguments=[
                    PromptArgument(
                        name="target_id",
                        description="ID of the target",
                        required=True
                    )
                ]
            )
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> list[PromptMessage]:
        """Get a prompt template with filled arguments."""
        logger.info(f"Prompt requested: {name} with arguments: {arguments}")

        if arguments is None:
            arguments = {}

        if name == "diagnostic_analysis":
            return _diagnostic_analysis_prompt(arguments)

        if name == "health_report":
            return _health_report_prompt(arguments)

        raise ValueError(f"Unknown prompt: {name}")


def _diagnostic_analysis_prompt(arguments: dict) -> list[PromptMessage]:
    """Generate diagnostic analysis prompt."""
    target_id = arguments.get("target_id", "unknown")
    problem_description = arguments.get("problem_description", "No description provided")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Analyze the following diagnostic data for target {target_id}.

## Problem Description
{problem_description}

## Instructions
1. Use the `diagnose` tool to collect diagnostic data
2. Analyze the findings
3. Provide a structured assessment with:
   - Summary of the situation
   - Identified issues (severity: critical/warning/normal)
   - Root cause analysis
   - Recommended actions

Please proceed with the analysis."""
            )
        )
    ]


def _health_report_prompt(arguments: dict) -> list[PromptMessage]:
    """Generate health report prompt."""
    target_id = arguments.get("target_id", "unknown")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Generate a health report for target {target_id}.

## Instructions
1. Use the `diagnose` tool to collect current status
2. Summarize the overall health
3. Highlight any areas of concern
4. Provide recommendations for improvement

Format the report in a clear, executive-friendly manner."""
            )
        )
    ]
