"""Configuration for {{AGENT_NAME}} agent."""

import os

# Agent Configuration
AGENT_NAME = "{{AGENT_NAME}}"
AGENT_VERSION = "0.1.0"

# Server Configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Add your custom configuration here
# API_URL = os.environ.get("API_URL", "https://api.example.com")
# API_KEY = os.environ.get("API_KEY", "")
