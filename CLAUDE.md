# EchoSphere - AI Agent Instructions

This file provides context for AI agents (Claude Code, Cursor, etc.) working on this project.

## Project Overview

**EchoSphere** is a real-time AI voice interaction platform with recording and playback capabilities.

### Name Meaning
- **Echo**: Real-time AI responses + recording/playback (voice echoing back)
- **Sphere**: Immersive interaction space + comprehensive data lifecycle management

### Core Features
1. **Real-time Voice Interaction**: Low-latency voice conversations with AI (LiveKit + LLM)
2. **Recording & Archiving**: Session recording with video composition
3. **ABR Playback**: Adaptive bitrate streaming for optimal playback experience
4. **LLM Observability**: Tracing, latency monitoring, evaluation

## Tech Stack

### Frontend (`apps/web/`)
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **Real-time**: LiveKit Client SDK
- **Video Player**: HLS.js
- **Linting**: Biome

### Backend (`apps/agent/`)
- **Framework**: LiveKit Agents (Python)
- **Language**: Python 3.12+
- **AI/ML**: OpenAI GPT-4o / Deepgram (STT) / ElevenLabs (TTS)
- **Validation**: Pydantic v2
- **Linting**: Ruff, Mypy (strict)

### Infrastructure
- **Media Processing**: LiveKit Egress, AWS MediaConvert
- **Storage**: AWS S3
- **CDN**: CloudFront
- **Observability**: OpenTelemetry, LangSmith

---

## Architecture Rules

### Backend: Hexagonal Architecture

```
domain/           <- Pure Python, ZERO external dependencies
application/      <- Use cases, depends only on domain
adapters/         <- External integrations (LiveKit, OpenAI, S3)
```

**Critical Rules:**
- `domain/` must have NO imports from external packages
- All external services accessed through adapters
- Use dependency injection for testability

### Frontend: Feature-Sliced Design

```
features/<name>/
├── components/   <- UI specific to this feature
├── hooks/        <- Logic and state
├── api/          <- Data fetching
└── types/        <- Type definitions
```

**Critical Rules:**
- Features must be self-contained
- No circular dependencies between features
- Shared code goes in `shared/`

---

## Coding Constraints

### Language Policy
**All code, comments, documentation, commits, and logs MUST be in English.**

### TypeScript Rules
- Use `async/await`, never `.then()` chains
- Explicit return types on all functions
- Use `interface` for objects, `type` for unions
- Prefer Server Components, minimize `useEffect`
- Use custom hooks to extract logic from components

### Python Rules
- Type hints required on ALL functions
- Use `asyncio` for all I/O (no blocking calls)
- Use `pydantic` for data validation
- Google Style Docstrings required
- No `requests` library - use `httpx`

### Error Handling
**Python:**
```python
# Define custom exceptions in domain layer
class DomainError(Exception):
    """Base for domain errors."""
    pass

# Include context
raise AudioProcessingError(f"Failed: {reason}", original_error=e)
```

**TypeScript:**
```typescript
// Use Result type for expected errors
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };
```

### Logging
- Structured JSON format (structlog/pino)
- Include `trace_id`, `span_id` for tracing
- Log levels: debug, info, warn, error

---

## Development Commands

```bash
task dev          # Start all services
task check        # Run linters and type checkers
task test         # Run all tests
task test:unit    # Run unit tests
task build        # Build all packages
```

---

## Common Patterns

### API Response Pattern (TypeScript)
```typescript
// Always return consistent shape
async function fetchRecordings(): Promise<Result<Recording[]>> {
  try {
    const data = await api.get('/recordings');
    return { success: true, data };
  } catch (error) {
    logger.error('Failed to fetch recordings', { error });
    return { success: false, error: error as Error };
  }
}
```

### Service Pattern (Python)
```python
class AudioProcessingService:
    """Application service for audio processing.

    Args:
        stt_adapter: Speech-to-text adapter implementation.
        logger: Structured logger instance.
    """

    def __init__(
        self,
        stt_adapter: STTPort,
        logger: structlog.BoundLogger,
    ) -> None:
        self._stt = stt_adapter
        self._logger = logger

    async def process(self, audio: AudioBuffer) -> TranscriptionResult:
        """Process audio and return transcription."""
        self._logger.info("processing_audio", size=len(audio.data))
        return await self._stt.transcribe(audio)
```

### Component Pattern (TypeScript)
```typescript
// Separate logic into hooks
function useVideoPlayer(recordingId: string) {
  const [state, setState] = useState<PlayerState>('loading');
  // ... logic
  return { state, play, pause, seek };
}

// Keep components focused on UI
function VideoPlayer({ recordingId }: Props) {
  const { state, play, pause } = useVideoPlayer(recordingId);
  return (/* UI only */);
}
```

---

## What NOT to Do

- **Don't** use `any` type in TypeScript
- **Don't** use blocking I/O in Python (requests, time.sleep)
- **Don't** put business logic in adapters
- **Don't** import from adapters in domain layer
- **Don't** hardcode configuration values
- **Don't** commit secrets or API keys
- **Don't** write Japanese in code/comments/commits
- **Don't** create files without clear purpose
- **Don't** skip tests for domain logic

---

## File Organization

When creating new files:

1. **Backend features** → `apps/agent/src/`
2. **Frontend features** → `apps/web/src/features/<name>/`
3. **Shared UI** → `apps/web/src/shared/components/`
4. **Types** → Co-locate with feature or in `shared/types/`
5. **Tests** → Adjacent to source (`__tests__/` or `.test.ts`)
6. **ADRs** → `docs/adr/NNN-title.md`

---

## Before You Code

1. Check if there's an existing pattern in the codebase
2. Read the relevant ADR if one exists
3. Ensure the Issue/RFC is clear
4. Write or update tests alongside code
5. Run `task check` before committing

---

## Questions to Ask Yourself

- Is this in the right architectural layer?
- Are there tests for this logic?
- Will this break existing functionality?
- Is the error handling appropriate?
- Is this observable (logging, tracing)?
