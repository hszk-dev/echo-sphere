# EchoSphere Agent

Python-based AI voice agent using LiveKit Agents framework.

## Architecture

This agent follows Hexagonal Architecture (Ports & Adapters):

```
src/
├── domain/           # Pure business logic (no external dependencies)
├── application/      # Use cases and port interfaces
├── adapters/         # External service implementations
└── config/           # Configuration and logging
```

## Development

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Run linter
uv run ruff check src tests

# Run type checker
uv run mypy src

# Run tests
uv run pytest
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `OPENAI_API_KEY`: OpenAI API key
