# DataOrb

Raspberry Pi dashboard that displays PostHog analytics on a round HyperPixel LCD.

## Build Commands

```bash
make dev        # Start development servers (backend + frontend)
make build      # Production build
make lint       # Run all linters
make test       # Run quality checks
make deploy     # Deploy to Pi via Ansible
```

## Critical Rules

- Pin dependencies to exact versions
- Keep docs updated with every code change
- Keep Makefile updated — add new tasks as project evolves
- Never commit .env files or API keys — use Ansible Vault for secrets
- WiFi AP default passwords must use environment variables, not hardcoded values

## Detailed Guides

| Topic | Guide |
|-------|-------|
| Quick Start | [docs/QUICK_START.md](docs/QUICK_START.md) |
| Architecture Decisions | [docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) |
| Pi 5 Setup | [docs/PI5_SETUP.md](docs/PI5_SETUP.md) |
| OTA Updates | [docs/OTA_README.md](docs/OTA_README.md) |
| API | [docs/api.md](docs/api.md) |
