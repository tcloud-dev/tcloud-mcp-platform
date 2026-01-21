# Task Completion Checklist

## Adding New Helm Values

- [ ] Add to `values.yaml` (base config)
- [ ] Add environment-specific overrides to `values-dev.yaml` and `values-prod.yaml` if needed
- [ ] Update documentation if it's a user-facing change
- [ ] Test with `make template ENV=dev` to verify rendering

## Creating a New Agent Template

- [ ] Add template files under `templates/`
- [ ] Use `{{AGENT_NAME}}` placeholder for agent name
- [ ] Include Dockerfile, docker-compose.yml, requirements.txt
- [ ] Include src/ with server.py, tools.py, prompts.py, config.py
- [ ] Include tests/ directory
- [ ] Include README.md with usage instructions
- [ ] Update `docs/creating-agents.md` if needed

## Documentation Changes

- [ ] Update relevant .md files in docs/
- [ ] Update README.md if it affects main usage
- [ ] Check all internal links work

## Infrastructure Changes

- [ ] Test in dev environment first
- [ ] Verify health checks pass
- [ ] Check logs for errors
- [ ] Update values-prod.yaml only after dev validation

## Before Committing

- [ ] Run `make validate` to check Helm syntax
- [ ] Verify no secrets are committed
- [ ] Write clear commit message with conventional commit prefix
