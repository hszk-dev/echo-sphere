# Contributing to EchoSphere

Welcome to EchoSphere! This document outlines the development workflow, coding standards, and governance rules for contributing to this project.

## Table of Contents

- [Language Policy](#language-policy)
- [Development Workflow](#development-workflow)
- [Git Conventions](#git-conventions)
- [Architecture Rules](#architecture-rules)
- [Coding Standards](#coding-standards)
- [Testing Strategy](#testing-strategy)
- [Code Review Guidelines](#code-review-guidelines)

---

## Language Policy

**All project artifacts MUST be in English:**

- Source code (comments, variable names, function names)
- Documentation (README, ADRs, inline docs)
- Commit messages and PR descriptions
- Issue titles and descriptions
- Log messages and error messages

---

## Development Workflow

We follow a **Design-First** development lifecycle:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Issue     │────▶│    ADR      │────▶│  Detailed   │────▶│    TDD /    │────▶│   Review    │
│ Definition  │     │ (if needed) │     │   Design    │     │Implementation│     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 1. Issue Definition

- Create an Issue using the appropriate template
- Define the problem/feature clearly
- Include acceptance criteria

### 2. ADR (Architecture Decision Record)

- Required for significant technical decisions
- Located in `docs/adr/`
- Follow the ADR template

### 3. Detailed Design (RFC)

- Define interfaces, data structures, and flow
- Include in the Issue or a separate design doc
- Must be approved before implementation

### 4. TDD / Implementation

- Write tests first (or concurrently)
- Implement following architecture rules
- Keep commits atomic

### 5. Review

- Self-review before requesting review
- Address all CI failures
- Ensure design compliance

---

## Git Conventions

### Branch Naming

```
<type>/<issue-number>-<short-description>
```

**Types:**
- `feat/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

**Examples:**
- `feat/12-video-player-ui`
- `fix/45-audio-sync-issue`
- `refactor/78-extract-media-service`

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code change that neither fixes a bug nor adds a feature
- `docs` - Documentation only changes
- `test` - Adding or correcting tests
- `chore` - Maintenance tasks
- `perf` - Performance improvement
- `ci` - CI/CD changes

**Scope (optional):**
- `web` - Frontend (Next.js)
- `agent` - Backend (Python/LiveKit Agents)
- `infra` - Infrastructure
- `docs` - Documentation

**Examples:**
```
feat(web): add video player component with HLS support

fix(agent): resolve audio buffer overflow in STT processing

refactor(web): extract media controls into custom hook

docs: add ADR for HLS streaming decision
```

### Atomic Commits

Each commit should:
- Do ONE thing only
- Be independently reviewable
- Pass all tests
- Not break the build

### Branching Strategy (Trunk-Based)

- `main` - Protected, always deployable
- Feature branches - Short-lived (< 3 days)
- Merge via PR with required reviews

---

## Architecture Rules

### Backend (Python) - Hexagonal Architecture

```
apps/agent/src/
├── domain/           # Pure business logic (no external dependencies)
│   ├── entities/     # Domain entities
│   ├── value_objects/# Immutable value objects
│   └── services/     # Domain services
├── application/      # Use cases and application services
│   ├── use_cases/    # Application use cases
│   └── ports/        # Interface definitions (abstract)
├── adapters/         # External integrations
│   ├── inbound/      # Entry points (LiveKit workers, API)
│   └── outbound/     # External services (OpenAI, S3, DB)
└── config/           # Configuration management
```

**Rules:**
- `domain/` has ZERO external dependencies
- `application/` depends only on `domain/`
- `adapters/` implements interfaces defined in `application/ports/`
- Dependencies flow inward only

### Frontend (TypeScript) - Feature-Sliced Design

```
apps/web/src/
├── app/              # Next.js App Router pages
├── features/         # Feature modules
│   └── <feature>/
│       ├── components/   # Feature-specific UI
│       ├── hooks/        # Feature-specific logic
│       ├── api/          # Data fetching
│       └── types/        # Feature-specific types
├── shared/           # Shared utilities
│   ├── components/   # Reusable UI components
│   ├── hooks/        # Shared hooks
│   ├── lib/          # Utilities
│   └── types/        # Shared types
└── config/           # App configuration
```

**Rules:**
- Features are isolated and self-contained
- Shared code goes in `shared/`
- No circular dependencies between features

---

## Coding Standards

### TypeScript

- **Strict mode enabled** (`strict: true` in tsconfig)
- Use `interface` for object shapes, `type` for unions/intersections
- Prefer `const` over `let`, never use `var`
- Use `async/await` (no `.then()` chains)
- All functions must have explicit return types
- Use early returns to reduce nesting

### Python

- **Type hints required** for all functions
- Use `pydantic` for data validation
- Use `asyncio` for all I/O operations
- No blocking calls (use `httpx`, not `requests`)
- Follow Google Style Docstrings

**Docstring Example:**
```python
def process_audio(audio_buffer: bytes, sample_rate: int = 16000) -> ProcessingResult:
    """Process raw audio data to extract voice features.

    Args:
        audio_buffer: The raw audio stream data in PCM format.
        sample_rate: Audio sample rate in Hz. Defaults to 16000.

    Returns:
        ProcessingResult containing speech probability and timestamps.

    Raises:
        AudioFormatError: If the buffer is not in a supported format.
        ProcessingTimeoutError: If processing exceeds the timeout limit.
    """
```

### Error Handling

**Python:**
```python
# Use custom exceptions for domain errors
class DomainError(Exception):
    """Base exception for domain errors."""
    pass

class AudioProcessingError(DomainError):
    """Raised when audio processing fails."""
    pass

# Always include context in exceptions
raise AudioProcessingError(f"Failed to process audio: {reason}")
```

**TypeScript:**
```typescript
// Use Result pattern for expected errors
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

// Use try-catch for unexpected errors with proper typing
try {
  // operation
} catch (error) {
  logger.error('Operation failed', { error });
  throw error;
}
```

### Logging

- Use structured JSON logging
- Always include `trace_id` and `span_id` for distributed tracing
- Log levels: `debug`, `info`, `warn`, `error`

**Python (structlog):**
```python
import structlog

logger = structlog.get_logger()
logger.info("audio_processed", duration_ms=150, sample_count=1024)
```

**TypeScript (pino):**
```typescript
import pino from 'pino';

const logger = pino();
logger.info({ durationMs: 150, sampleCount: 1024 }, 'audio_processed');
```

### Configuration

- Use environment variables for all configuration
- Type-safe configuration loading
- Never commit secrets

**Python (pydantic-settings):**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    livekit_url: str
    livekit_api_key: str
    openai_api_key: str

    class Config:
        env_file = ".env"
```

---

## Testing Strategy

### Test Pyramid

```
        ╱╲
       ╱  ╲
      ╱ E2E╲        <- Few, critical paths only
     ╱──────╲
    ╱        ╲
   ╱Integration╲    <- API boundaries, adapters
  ╱────────────╲
 ╱              ╲
╱   Unit Tests   ╲  <- Domain logic, utilities (80%+ coverage)
╱────────────────╲
```

### Unit Tests

- **Coverage target:** >80% for domain logic
- Fast execution (<100ms per test)
- No external dependencies (mock everything)
- One assertion per test (ideally)

**Tools:**
- Python: `pytest`, `pytest-mock`, `pytest-asyncio`
- TypeScript: `vitest`

### Integration Tests

- Test adapter implementations
- Use Docker Compose for dependencies
- Test API contracts

**Tools:**
- Python: `pytest` with Docker fixtures
- TypeScript: `vitest` with MSW (Mock Service Worker)

### E2E Tests

- Critical user paths only
- Run in CI before merge
- Use realistic data

**Tools:**
- Playwright for browser testing
- Test the complete flow: Room entry → Recording → Playback

### Running Tests

```bash
# Run all tests
task test

# Run unit tests only
task test:unit

# Run with coverage
task test:coverage
```

---

## Code Review Guidelines

### Author Responsibilities

1. Self-review before requesting review
2. Ensure CI passes
3. Keep PRs small and focused
4. Respond to feedback promptly

### Reviewer Responsibilities

1. Review within 24 hours
2. Be constructive and specific
3. Approve only when satisfied
4. Focus on:
   - Architecture compliance
   - Test coverage
   - Error handling
   - Security implications

### Review Checklist

- [ ] Code follows architecture rules
- [ ] Tests are adequate and meaningful
- [ ] Error handling is appropriate
- [ ] No security vulnerabilities
- [ ] Performance implications considered
- [ ] Documentation updated if needed

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `task dev` | Start development environment |
| `task check` | Run all linters and type checks |
| `task test` | Run all tests |
| `task test:unit` | Run unit tests only |
| `task build` | Build all packages |

---

## Questions?

If you have questions about contributing, please open an Issue with the `question` label.
