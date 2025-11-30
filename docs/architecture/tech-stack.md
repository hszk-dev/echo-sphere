# EchoSphere - Technology Stack

## Overview

This document defines the exact technologies and versions used in EchoSphere. All contributors and AI agents must adhere to these specifications.

## Frontend (`apps/web/`)

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.x | React framework with App Router |
| React | 19.x | UI library |
| TypeScript | 5.x | Type-safe JavaScript |

### UI & Styling

| Technology | Version | Purpose |
|------------|---------|---------|
| Tailwind CSS | 3.x | Utility-first CSS |
| shadcn/ui | latest | Component library (copy-paste) |
| Radix UI | latest | Accessible primitives |
| Lucide React | latest | Icons |

### Real-time & Media

| Technology | Version | Purpose |
|------------|---------|---------|
| @livekit/components-react | latest | LiveKit React components |
| livekit-client | latest | LiveKit client SDK |
| hls.js | latest | HLS video playback |

### State & Data

| Technology | Version | Purpose |
|------------|---------|---------|
| TanStack Query | 5.x | Server state management |
| Zustand | 4.x | Client state (if needed) |
| Zod | 3.x | Runtime validation |

### Development Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| Biome | latest | Linting & formatting (replaces ESLint/Prettier) |
| Vitest | latest | Unit testing |
| Playwright | latest | E2E testing |
| MSW | latest | API mocking |

## Backend (`apps/agent/`)

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Runtime |
| livekit-agents | latest | Agent framework |
| livekit | latest | LiveKit Python SDK |

### AI/ML Services (AWS)

| Technology | Version | Model/Config | Purpose |
|------------|---------|--------------|---------|
| livekit-plugins-aws | ~1.2 | - | AWS integration for LiveKit Agents |
| Amazon Transcribe | - | ja-JP (streaming) | Speech-to-Text |
| Amazon Bedrock | - | Claude Sonnet 4.5 | LLM for conversation |
| Amazon Polly | - | Kazuha (neural) | Text-to-Speech (Japanese)

#### AWS Bedrock Model IDs

Bedrock requires Cross-Region Inference. Use region-prefixed model IDs:

| Region | Model ID |
|--------|----------|
| US | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| EU | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| APAC | `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` |

For `ap-northeast-1` (Tokyo), use the APAC prefix.

### Data & Validation

| Technology | Version | Purpose |
|------------|---------|---------|
| Pydantic | 2.x | Data validation |
| pydantic-settings | 2.x | Configuration management |
| SQLAlchemy | 2.x | ORM (async) |
| asyncpg | latest | PostgreSQL async driver |

### HTTP & Async

| Technology | Version | Purpose |
|------------|---------|---------|
| httpx | latest | Async HTTP client |
| aiofiles | latest | Async file I/O |

### Development Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| Ruff | latest | Linting & formatting |
| Mypy | latest | Static type checking |
| pytest | latest | Testing framework |
| pytest-asyncio | latest | Async test support |
| pytest-cov | latest | Coverage reporting |

### Observability

| Technology | Version | Purpose |
|------------|---------|---------|
| structlog | latest | Structured logging |
| opentelemetry-sdk | latest | Distributed tracing |
| opentelemetry-instrumentation-* | latest | Auto-instrumentation |

## Infrastructure

### AWS Services

| Service | Purpose |
|---------|---------|
| S3 | Media storage (raw + processed) |
| CloudFront | CDN for media delivery |
| MediaConvert | Video transcoding |
| SQS | Message queue for async processing |
| Lambda | Event-driven workers |
| RDS (PostgreSQL) | Metadata database |

### AWS AI Services

| Service | Model/Config | Purpose |
|---------|--------------|---------|
| Amazon Transcribe | ja-JP streaming | Real-time speech recognition |
| Amazon Bedrock | Claude Sonnet 4.5 | LLM for conversation |
| Amazon Polly | Kazuha (neural) | Japanese text-to-speech |

### Infrastructure as Code

| Technology | Version | Purpose |
|------------|---------|---------|
| Pulumi | latest | Infrastructure definition (TypeScript) |

### Containerization

| Technology | Version | Purpose |
|------------|---------|---------|
| Docker | latest | Container runtime |
| Docker Compose | latest | Local development |

## Observability Stack

| Technology | Purpose |
|------------|---------|
| OpenTelemetry | Unified telemetry collection |
| LangSmith | LLM observability |
| Grafana | Metrics visualization |
| Prometheus | Metrics collection |

## Development Environment

### Package Managers

| Technology | Purpose |
|------------|---------|
| pnpm | Node.js package manager |
| uv | Python package manager |

### Monorepo Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| Turborepo | latest | Monorepo build system |
| Task | latest | Task runner (Makefile alternative) |

## Version Pinning Policy

1. **Major versions** are pinned explicitly (e.g., `next@15`)
2. **Minor versions** allowed to float for patches
3. **Lock files** committed (`pnpm-lock.yaml`, `uv.lock`)
4. **Renovate/Dependabot** for automated updates

## Prohibited Technologies

The following are explicitly NOT used:

| Technology | Reason |
|------------|--------|
| `requests` (Python) | Blocking I/O, use `httpx` |
| `express` (Node.js) | Using Next.js API routes |
| jQuery | Modern React patterns |
| Redux | Overkill, use Zustand if needed |
| Moment.js | Deprecated, use native Date or date-fns |
| ESLint + Prettier | Replaced by Biome |
| `openai` (Python) | Using AWS Bedrock for LLM |
| `deepgram-sdk` | Using Amazon Transcribe |
| `elevenlabs` | Using Amazon Polly |

## Configuration Files

```
echo-sphere/
├── biome.json           # Frontend linting/formatting
├── turbo.json           # Turborepo configuration
├── Taskfile.yaml        # Task runner commands
├── docker-compose.yml   # Local services
├── apps/
│   ├── web/
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   └── tailwind.config.ts
│   └── agent/
│       ├── pyproject.toml
│       ├── ruff.toml
│       └── mypy.ini
└── packages/
    └── config/          # Shared configurations
```
