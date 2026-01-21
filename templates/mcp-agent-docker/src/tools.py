"""MCP Tools for {{AGENT_NAME}} agent.

This is where you implement your agent's tools (functions).
Each tool should:
1. Be listed in list_tools()
2. Be handled in call_tool()

Example tools are provided below - replace them with your own.
"""

import json
import logging
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def register(server: Server):
    """Register tools with the MCP server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name="example_tool",
                description="An example tool - replace with your own",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "A message to process"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="diagnose",
                description="Run diagnostic analysis and return structured result",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target_id": {
                            "type": "string",
                            "description": "ID of the target to diagnose"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context about the problem"
                        }
                    },
                    "required": ["target_id"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool and return results."""
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "example_tool":
            return await _example_tool(arguments)

        if name == "diagnose":
            return await _diagnose(arguments)

        raise ValueError(f"Unknown tool: {name}")


async def _example_tool(arguments: dict) -> list[TextContent]:
    """Example tool implementation."""
    message = arguments.get("message", "")

    result = {
        "status": "success",
        "processed_message": message.upper(),
        "timestamp": datetime.utcnow().isoformat()
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def _diagnose(arguments: dict) -> list[TextContent]:
    """
    Diagnostic tool implementation.

    Returns a standardized micro-diagnostic format that can be
    consolidated by the orchestrator agent.
    """
    target_id = arguments.get("target_id")
    context = arguments.get("context", "")

    # TODO: Implement your diagnostic logic here
    # This is a placeholder that returns a sample diagnostic

    diagnostic = {
        "agent": "{{AGENT_NAME}}",
        "timestamp": datetime.utcnow().isoformat(),
        "target_id": target_id,
        "severity": "normal",  # critical | warning | normal
        "summary": "No issues detected",
        "findings": [
            {
                "type": "example_check",
                "severity": "normal",
                "details": "All checks passed",
                "evidence": {
                    "checked_at": datetime.utcnow().isoformat()
                }
            }
        ],
        "recommendations": [],
        "raw_data": {
            "context_provided": context
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(diagnostic, indent=2, ensure_ascii=False)
    )]
