# EchoSphere

Real-time AI voice interaction platform with recording and playback capabilities.

## Overview

**EchoSphere** combines real-time voice AI with comprehensive session recording and adaptive bitrate playback.

- **Echo**: Real-time AI responses + recording/playback (voice echoing back)
- **Sphere**: Immersive interaction space + comprehensive data lifecycle management

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15, React 19, TypeScript |
| Backend | Python 3.12+, LiveKit Agents |
| Real-time | LiveKit, WebRTC |
| AI | OpenAI GPT-4o, Deepgram, ElevenLabs |
| Storage | PostgreSQL, S3, Redis |
| Observability | OpenTelemetry, LangSmith |

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- pnpm 9+
- uv (Python package manager)
- Docker & Docker Compose
- Task (task runner)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/echo-sphere.git
cd echo-sphere

# Copy environment variables
cp .env.example .env

# Install dependencies
task setup

# Start development services
task dev
```

### LiveKit Local Development

For local development, **native LiveKit server installation is recommended** over Docker.

> **Why not Docker?**
> According to the [official LiveKit documentation](https://docs.livekit.io/home/self-hosting/deployment/):
>
> *"WebRTC servers can be tricky to deploy because of their use of UDP ports and having to know their own public IP address."*
>
> *"If running in a Dockerized environment, host networking should be used for optimal performance."*
>
> On macOS, Docker's `--network host` mode requires Docker Desktop 4.34+ with explicit enablement, and [known issues remain](https://github.com/docker/for-mac/issues/7448). This causes WebRTC peer connections to fail.

**Install and run LiveKit natively:**

```bash
# macOS
brew install livekit

# Start in development mode
livekit-server --dev
# API Key: devkey
# API Secret: secret
```

The Docker Compose configuration includes LiveKit for reference, but use the native installation for reliable WebRTC connections on macOS.

### Commands

```bash
# Development
task dev          # Start all services
task dev:web      # Start frontend only
task dev:agent    # Start backend only

# Code Quality
task check        # Run all linters
task fix          # Auto-fix issues

# Testing
task test         # Run all tests
task test:unit    # Run unit tests
task test:coverage # Run with coverage

# Docker
task docker:up    # Start services
task docker:down  # Stop services
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EchoSphere                            │
├─────────────────────────────────────────────────────────┤
│  Pipeline 1: Real-time Interaction (LiveKit + AI)       │
│  Pipeline 2: Media Processing (S3 → HLS)                │
│  Pipeline 3: Intelligence & Observability               │
└─────────────────────────────────────────────────────────┘
```

See [docs/architecture/system-overview.md](docs/architecture/system-overview.md) for details.

## Project Structure

```
echo-sphere/
├── apps/
│   ├── web/           # Next.js frontend
│   └── agent/         # Python LiveKit agent
├── packages/
│   └── config/        # Shared configurations
├── docs/
│   ├── architecture/  # System design docs
│   └── adr/           # Architecture decisions
├── Taskfile.yaml      # Task runner commands
└── docker-compose.yml # Local services
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and coding standards.

## License

MIT
