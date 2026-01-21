"""MCP Server for {{AGENT_NAME}} agent."""

import logging
import json
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from mcp.server import Server
from mcp.server.sse import SseServerTransport

from src.config import AGENT_NAME, AGENT_VERSION, HOST, PORT, LOG_LEVEL
from src import tools
from src import prompts

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp_server = Server(AGENT_NAME)

# Register tools and prompts
tools.register(mcp_server)
prompts.register(mcp_server)


async def health(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION
    })


async def handle_sse(request):
    """Handle SSE MCP connections."""
    logger.info(f"New SSE connection from {request.client.host}")

    sse_transport = SseServerTransport("/mcp/messages")

    async with sse_transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options()
        )

    return Response()


async def handle_messages(request):
    """Handle SSE message posting."""
    body = await request.body()
    logger.debug(f"Received message: {body.decode()}")

    # The SSE transport handles this internally
    return Response(status_code=202)


# Create Starlette app
app = Starlette(
    debug=LOG_LEVEL == "DEBUG",
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/mcp", handle_sse, methods=["GET"]),
        Route("/mcp/messages", handle_messages, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    logger.info(f"Starting {AGENT_NAME} v{AGENT_VERSION} on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
