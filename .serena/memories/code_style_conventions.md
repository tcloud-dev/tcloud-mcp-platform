# Code Style Conventions

## Helm Values

- Use kebab-case for Helm value keys
- Group related settings under parent keys
- Always provide comments for non-obvious settings
- Sensitive values should reference external secrets in prod

```yaml
# Good
gateway:
  replicaCount: 2
  resources:
    requests:
      memory: "256Mi"

# Bad
gatewayReplicaCount: 2
gatewayMemory: "256Mi"
```

## MCP Agent Template (Python)

- Follow PEP 8
- Use type hints
- Use async/await for all MCP handlers
- Return structured JSON for diagnostic tools

### Tool Response Format

All diagnostic tools must return this standardized format:

```python
{
    "agent": "agent-name",
    "timestamp": "ISO8601",
    "severity": "critical|warning|normal",
    "summary": "One-line summary",
    "findings": [
        {
            "type": "finding_type",
            "severity": "critical|warning|normal",
            "details": "Description",
            "evidence": {}
        }
    ],
    "recommendations": ["Action 1", "Action 2"],
    "raw_data": {}  # Optional
}
```

### Logging

Use structured JSON logging:

```python
import logging
import json

logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "event": "tool_call",
    "tool": name,
    "arguments": arguments
}))
```

## Documentation

- Use Markdown for all docs
- Include code examples
- Keep README.md concise, link to docs/ for details
- Use tables for comparisons and lists

## Git

- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`
- Keep commits atomic and focused
- Write descriptive commit messages
