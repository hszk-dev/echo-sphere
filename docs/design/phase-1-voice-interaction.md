# Phase 1: Core Voice Interaction - Design Document

**Status**: Draft
**Date**: 2024-11-30
**Author**: AI Assistant
**Reviewers**: Project Owner

## 1. Executive Summary

Phase 1 establishes the foundation for EchoSphere's real-time voice AI interaction capability. This phase delivers a working voice assistant with sub-second latency, demonstrating L5-level engineering practices including clean architecture, observability, and comprehensive testing.

### Key Deliverables
- LiveKit Agent with STT → LLM → TTS pipeline (AWS services)
- Next.js frontend with voice room UI
- Token generation API
- Japanese language support from day one
- OpenTelemetry tracing integration
- Unit and integration tests for domain logic

### Success Criteria
- Voice-to-Voice latency: < 1.5 seconds (P95) - adjusted for AWS service latency
- Agent availability: 99%+ during development
- Test coverage: > 80% for domain layer

### Decisions Made
- **AI Services**: Use AWS (Transcribe, Bedrock, Polly) instead of LiveKit Inference
- **Avatar**: Not included in Phase 1 (deferred to Phase 3)
- **Language**: Japanese support from Phase 1

---

## 2. Current State Analysis

### What Exists (✅ Complete)
| Component | Details |
|-----------|---------|
| Monorepo structure | pnpm workspaces + Turborepo |
| Task runner | Taskfile.yaml with dev, check, test commands |
| Backend scaffold | Hexagonal Architecture structure |
| Configuration | pydantic-settings with LiveKit/OpenAI keys |
| Logging | structlog with JSON output |
| Domain entity | Session with state machine |
| Ports | STTPort, LLMPort, TTSPort interfaces defined |
| Frontend scaffold | Next.js 15 + Tailwind CSS |

### What's Missing (❌ Phase 1 Scope)
| Component | Priority | Complexity |
|-----------|----------|------------|
| LiveKit Agent Worker | P0 | High |
| AI Pipeline (AWS STT/LLM/TTS) | P0 | Medium |
| Voice Room UI | P0 | Medium |
| Token Generation API | P0 | Low |
| Session Data Storage | P1 | Medium |
| OpenTelemetry Tracing | P1 | Medium |
| Integration Tests | P1 | Medium |

---

## 3. AI Services Architecture

### 3.1 AWS Services Selection

Phase 1 uses AWS services to avoid per-API-call charges from third-party providers:

| Component | Service | Japanese Support | Cost Model |
|-----------|---------|------------------|------------|
| **STT** | Amazon Transcribe | ✅ `ja-JP` | Per-second streaming |
| **LLM** | Amazon Bedrock (Claude 3.5 Sonnet) | ✅ Native | Per-token |
| **TTS** | Amazon Polly | ✅ `Kazuha` (neural), `Takumi`, `Mizuki` | Per-character |

### 3.2 Why AWS?

1. **Cost Predictability**: AWS services integrate with existing infrastructure billing
2. **Japanese Excellence**: Amazon Transcribe and Polly have strong Japanese support
3. **Unified Auth**: Single AWS credentials for all AI services
4. **Region Control**: Deploy in `ap-northeast-1` (Tokyo) for lowest latency

### 3.3 Service Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Pipeline Comparison                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LiveKit Inference (Original)      AWS Services (Selected)       │
│  ┌─────────────────────────┐      ┌─────────────────────────┐   │
│  │ AssemblyAI (STT)        │  →   │ Amazon Transcribe       │   │
│  │ OpenAI GPT-4.1-mini     │  →   │ Bedrock Claude 3.5      │   │
│  │ Cartesia Sonic (TTS)    │  →   │ Amazon Polly Neural     │   │
│  └─────────────────────────┘      └─────────────────────────┘   │
│                                                                  │
│  Pros: Lower latency              Pros: Cost control, JP support │
│  Cons: Per-API billing            Cons: Slightly higher latency  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Architecture

### 4.1 Backend Architecture (Python)

```
apps/agent/src/
├── domain/
│   ├── entities/
│   │   ├── session.py          # ✅ Exists
│   │   └── message.py          # NEW: Conversation message
│   ├── value_objects/
│   │   ├── transcript.py       # NEW: Immutable transcript
│   │   └── audio_frame.py      # NEW: Audio data wrapper
│   └── services/
│       └── conversation.py     # NEW: Conversation logic
├── application/
│   ├── ports/
│   │   ├── stt_port.py        # ✅ Exists
│   │   ├── llm_port.py        # ✅ Exists
│   │   └── tts_port.py        # ✅ Exists
│   └── use_cases/
│       └── voice_session.py   # NEW: Voice session orchestration
├── adapters/
│   ├── inbound/
│   │   └── livekit_worker.py  # NEW: LiveKit Agent entrypoint
│   └── outbound/
│       ├── aws_stt.py         # NEW: Amazon Transcribe adapter
│       ├── aws_llm.py         # NEW: Amazon Bedrock adapter
│       └── aws_tts.py         # NEW: Amazon Polly adapter
├── config/
│   ├── settings.py            # ✅ Exists (extend)
│   ├── logging.py             # ✅ Exists
│   └── tracing.py             # NEW: OpenTelemetry setup
└── main.py                    # ✅ Exists (update)
```

### 4.2 Agent Session Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentSession                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌───────────┐    ┌─────────┐    ┌────────┐ │
│  │   VAD   │───▶│    STT    │───▶│   LLM   │───▶│  TTS   │ │
│  │ (Silero)│    │(Transcribe│    │(Bedrock │    │(Polly) │ │
│  └─────────┘    │  ja-JP)   │    │ Claude) │    │Kazuha) │ │
│                 └───────────┘    └─────────┘    └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      RoomIO                                  │
│   (Audio Input/Output, Transcription, Noise Cancellation)   │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Frontend Architecture (TypeScript)

```
apps/web/src/
├── app/
│   ├── layout.tsx             # ✅ Exists
│   ├── page.tsx               # ✅ Exists (update: add navigation)
│   ├── room/
│   │   └── [roomId]/
│   │       └── page.tsx       # NEW: Voice room page
│   └── api/
│       └── token/
│           └── route.ts       # NEW: Token generation endpoint
├── features/
│   └── voice-room/
│       ├── components/
│       │   ├── VoiceRoom.tsx           # NEW: Main room component
│       │   ├── AudioVisualizer.tsx     # NEW: Agent state visualizer
│       │   ├── TranscriptPanel.tsx     # NEW: Real-time transcript
│       │   └── ConnectionStatus.tsx    # NEW: Connection indicator
│       ├── hooks/
│       │   ├── useVoiceSession.ts      # NEW: Session management
│       │   └── useTranscript.ts        # NEW: Transcript sync
│       ├── types/
│       │   └── index.ts                # NEW: Feature types
│       └── index.ts                    # NEW: Public exports
├── shared/
│   ├── components/
│   │   └── ui/                # NEW: shadcn/ui components
│   ├── lib/
│   │   ├── livekit.ts         # NEW: LiveKit client setup
│   │   └── logger.ts          # ✅ Exists
│   └── types/
│       └── result.ts          # ✅ Exists
└── config/
    └── env.ts                 # NEW: Environment config
```

---

## 5. Component Design

### 5.1 Agent Worker with AWS Services (Python)

```python
# apps/agent/src/adapters/inbound/livekit_worker.py
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import aws, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.config.settings import get_settings


class EchoSphereAssistant(Agent):
    """EchoSphere voice AI assistant with Japanese support.

    Attributes:
        session_id: Unique session identifier for tracing.
    """

    def __init__(self, session_id: str) -> None:
        super().__init__(
            instructions="""You are EchoSphere, a helpful voice AI assistant.
            You can speak both Japanese and English fluently.
            You provide concise, clear responses without complex formatting.
            You are friendly, curious, and have a sense of humor.
            Respond in the same language the user speaks to you.""",
        )
        self.session_id = session_id


server = AgentServer()


@server.rtc_session()
async def voice_agent(ctx: agents.JobContext) -> None:
    """Voice agent entrypoint with AWS services.

    Args:
        ctx: LiveKit job context with room and participant info.
    """
    settings = get_settings()

    # Configure AWS-based AI pipeline
    session = AgentSession(
        stt=aws.STT(
            language=settings.stt_language,  # "ja-JP" or "en-US"
            speech_region=settings.aws_region,
        ),
        llm=aws.LLM(
            model=settings.llm_model,  # "anthropic.claude-3-5-sonnet-20240620-v1:0"
            region=settings.aws_region,
            temperature=0.7,
        ),
        tts=aws.TTS(
            voice=settings.tts_voice,  # "Kazuha" for Japanese
            speech_engine="neural",
            language=settings.tts_language,  # "ja-JP"
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=EchoSphereAssistant(session_id=str(ctx.room.name)),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    # Bilingual greeting
    await session.generate_reply(
        instructions="Greet the user warmly in Japanese. Introduce yourself as EchoSphere (エコスフィア)."
    )
```

### 5.2 Japanese Voice Configuration

**Amazon Polly Japanese Voices:**

| Voice | Gender | Engine | Quality | Recommended |
|-------|--------|--------|---------|-------------|
| **Kazuha** | Female | Neural | Best | ✅ Primary |
| Takumi | Male | Neural | Good | Alternative |
| Mizuki | Female | Standard | Okay | Fallback |

**Amazon Transcribe Japanese:**
- Language code: `ja-JP`
- Streaming: Supported
- Custom vocabulary: Available for domain-specific terms

### 5.3 Token Generation API (TypeScript)

```typescript
// apps/web/src/app/api/token/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

export const revalidate = 0;

interface TokenRequest {
  roomName: string;
  participantName: string;
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  const body: TokenRequest = await req.json();

  const { roomName, participantName } = body;

  if (!roomName || !participantName) {
    return NextResponse.json(
      { error: 'Missing roomName or participantName' },
      { status: 400 }
    );
  }

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;

  if (!apiKey || !apiSecret) {
    return NextResponse.json(
      { error: 'Server misconfigured' },
      { status: 500 }
    );
  }

  const token = new AccessToken(apiKey, apiSecret, {
    identity: participantName,
    ttl: '10m',
  });

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  return NextResponse.json(
    { token: await token.toJwt() },
    { headers: { 'Cache-Control': 'no-store' } }
  );
}
```

### 5.4 Voice Room Component (React)

```tsx
// apps/web/src/features/voice-room/components/VoiceRoom.tsx
'use client';

import { useEffect, useState } from 'react';
import {
  RoomContext,
  useVoiceAssistant,
  BarVisualizer,
} from '@livekit/components-react';
import { Room } from 'livekit-client';
import '@livekit/components-styles';

interface VoiceRoomProps {
  roomName: string;
  participantName: string;
}

export function VoiceRoom({ roomName, participantName }: VoiceRoomProps) {
  const [room] = useState(() => new Room({
    adaptiveStream: true,
    dynacast: true,
  }));
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function connect() {
      try {
        const response = await fetch('/api/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ roomName, participantName }),
        });

        const data = await response.json();

        if (!mounted) return;

        if (data.error) {
          setError(data.error);
          return;
        }

        await room.connect(process.env.NEXT_PUBLIC_LIVEKIT_URL!, data.token);
        setIsConnected(true);
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Connection failed');
        }
      }
    }

    connect();

    return () => {
      mounted = false;
      room.disconnect();
    };
  }, [room, roomName, participantName]);

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  if (!isConnected) {
    return <div>Connecting...</div>;
  }

  return (
    <RoomContext.Provider value={room}>
      <VoiceAssistantUI />
    </RoomContext.Provider>
  );
}

function VoiceAssistantUI() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="w-64 h-64">
        <BarVisualizer
          state={state}
          barCount={5}
          trackRef={audioTrack}
        />
      </div>
      <p className="mt-4 text-lg capitalize">{state}</p>
    </div>
  );
}
```

---

## 6. Session Data Storage

### 6.1 What is Session Data?

Session data refers to information generated during a voice interaction:

| Data Type | Description | Size | Use Case |
|-----------|-------------|------|----------|
| **Session Metadata** | Room ID, user ID, timestamps, duration | ~1KB | Analytics, history |
| **Conversation History** | Message sequence (user/AI turns) | ~10-50KB | Replay, evaluation |
| **Transcripts** | Full text of spoken words | ~5-20KB | Search, review |
| **Audio Recordings** | Raw audio (Phase 2 Egress) | ~1-5MB/min | Playback |
| **Evaluation Scores** | LLM-as-judge results (Phase 3) | ~2KB | Quality metrics |

### 6.2 Recommendation: Include Metadata + Conversations in Phase 1

**Rationale:**
1. **Low Effort**: Simple PostgreSQL tables, already in tech stack
2. **High Value**: Enables session history, basic analytics, debugging
3. **Foundation**: Required for Phase 2 (recording) and Phase 3 (evaluation)
4. **L5 Demonstration**: Shows data modeling and persistence design skills

### 6.3 Proposed Schema

```sql
-- Session metadata
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    language VARCHAR(10) DEFAULT 'ja-JP',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    audio_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_messages_session_id ON messages(session_id);
```

### 6.4 Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Worker                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  AgentSession Events                                         │
│  ├── on_session_start  → Create session record              │
│  ├── on_user_speech    → Store user message                 │
│  ├── on_agent_speech   → Store assistant message            │
│  └── on_session_end    → Update session status/duration     │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Session Repository                        │
│                  (application/ports/session_port.py)         │
├─────────────────────────────────────────────────────────────┤
│  + create_session(room_name, user_id) → Session             │
│  + update_session(session_id, status) → Session             │
│  + add_message(session_id, role, content) → Message         │
│  + get_session(session_id) → Session                        │
│  + list_sessions(user_id) → List[Session]                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Adapter                            │
│              (adapters/outbound/postgres_session.py)         │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 What to Defer

| Feature | Phase | Reason |
|---------|-------|--------|
| Audio storage (S3) | Phase 2 | Requires Egress pipeline |
| Evaluation scores | Phase 3 | Requires LLM-as-judge |
| Full-text search | Phase 2+ | Requires indexing setup |
| Analytics dashboard | Phase 2+ | Requires frontend work |

---

## 7. Configuration

### 7.1 Environment Variables

```bash
# .env.example (update)

# Application
APP_NAME=echo-sphere-agent
DEBUG=false
LOG_LEVEL=INFO

# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# AWS Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=ap-northeast-1

# Database (Phase 1)
DATABASE_URL=postgresql://user:pass@localhost:5432/echosphere

# Frontend (apps/web/.env.local)
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### 7.2 Settings Extension

```python
# apps/agent/src/config/settings.py (extend)
class Settings(BaseSettings):
    # ... existing fields ...

    # AWS Configuration
    aws_region: str = Field(default="ap-northeast-1")
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: SecretStr | None = Field(default=None)

    # AI Model Configuration (AWS)
    stt_language: str = Field(default="ja-JP")  # Japanese by default
    llm_model: str = Field(default="anthropic.claude-3-5-sonnet-20240620-v1:0")
    tts_voice: str = Field(default="Kazuha")  # Japanese neural voice
    tts_language: str = Field(default="ja-JP")

    # Agent Behavior
    agent_greeting: str = Field(
        default="こんにちは！エコスフィアです。何かお手伝いできることはありますか？"
    )
    max_response_tokens: int = Field(default=256)

    # Database
    database_url: str = Field(default="postgresql://localhost:5432/echosphere")

    # Observability
    otel_enabled: bool = Field(default=True)
    otel_service_name: str = Field(default="echo-sphere-agent")
```

---

## 8. Dependencies

### 8.1 Backend Dependencies (add to pyproject.toml)

```toml
[project]
dependencies = [
    # ... existing ...
    "livekit-agents[aws,silero,turn-detector]~=1.2",
    "livekit-plugins-noise-cancellation~=0.2",
    "python-dotenv>=1.0.0",
    "opentelemetry-exporter-otlp>=1.28.0",
    # Database
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
]
```

### 8.2 Frontend Dependencies (add to package.json)

```json
{
  "dependencies": {
    "@livekit/components-react": "^2.7.0",
    "livekit-client": "^2.7.0",
    "livekit-server-sdk": "^2.9.0",
    "@livekit/components-styles": "^1.1.0"
  }
}
```

---

## 9. Data Flow

### 9.1 Connection Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant TokenAPI
    participant LiveKit
    participant Agent
    participant Database

    User->>Frontend: Enter room
    Frontend->>TokenAPI: POST /api/token
    TokenAPI-->>Frontend: JWT token
    Frontend->>LiveKit: Connect with token
    LiveKit-->>Frontend: Connected
    LiveKit->>Agent: Dispatch agent
    Agent->>Database: Create session record
    Agent->>LiveKit: Join room
    Agent-->>Frontend: Agent joined (via participant event)
    Agent->>Frontend: Greeting audio (Japanese)
```

### 9.2 Voice Interaction Cycle with AWS

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant LiveKit
    participant Agent
    participant Transcribe as Amazon Transcribe
    participant Bedrock as Amazon Bedrock
    participant Polly as Amazon Polly
    participant DB as PostgreSQL

    User->>Frontend: Speak (Japanese)
    Frontend->>LiveKit: Audio stream
    LiveKit->>Agent: Audio frames
    Agent->>Transcribe: Transcribe (ja-JP)
    Transcribe-->>Agent: Japanese text
    Agent->>DB: Store user message
    Agent->>Bedrock: Generate response (Claude 3.5)
    Bedrock-->>Agent: Response text (streaming)
    Agent->>DB: Store assistant message
    Agent->>Polly: Synthesize (Kazuha voice)
    Polly-->>Agent: Audio chunks
    Agent->>LiveKit: Audio stream
    LiveKit->>Frontend: Audio playback
    Frontend->>User: AI Voice (Japanese)
```

---

## 10. Implementation Roadmap

### Week 1: Backend Foundation

| Day | Task | Output |
|-----|------|--------|
| 1 | Setup LiveKit Agents + AWS dependencies | Working dev environment |
| 2 | Implement basic agent worker | Agent joins room |
| 3 | Add AWS STT/LLM/TTS pipeline | Voice-to-voice working (JP) |
| 4 | Add session storage (PostgreSQL) | Sessions persisted |
| 5 | Add observability (logging, tracing) | Traces visible |

### Week 2: Frontend & Integration

| Day | Task | Output |
|-----|------|--------|
| 6 | Token API endpoint | Token generation works |
| 7 | Install LiveKit React components | Components available |
| 8 | Voice room UI | Basic room page |
| 9 | Audio visualizer + transcript | Full UX |
| 10 | Integration testing + domain tests | E2E flow verified |

---

## 11. Testing Strategy

### 11.1 Unit Tests (Domain Layer)

```python
# apps/agent/tests/domain/test_session.py
import pytest
from src.domain.entities.session import Session, SessionStatus

class TestSession:
    def test_session_starts_in_pending_status(self):
        session = Session(room_name="test-room", user_id="user-1")
        assert session.status == SessionStatus.PENDING

    def test_session_can_start_from_pending(self):
        session = Session(room_name="test-room", user_id="user-1")
        session.start()
        assert session.status == SessionStatus.ACTIVE

    def test_session_cannot_start_twice(self):
        session = Session(room_name="test-room", user_id="user-1")
        session.start()
        with pytest.raises(ValueError):
            session.start()
```

### 11.2 Integration Tests (AWS Services)

```python
# apps/agent/tests/integration/test_aws_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_transcribe_japanese():
    """Test Amazon Transcribe with Japanese audio."""
    with patch('livekit.plugins.aws.STT') as mock_stt:
        mock_stt.return_value.transcribe = AsyncMock(
            return_value="こんにちは"
        )
        # Test implementation
        result = await mock_stt.return_value.transcribe(b"audio_data")
        assert result == "こんにちは"
```

---

## 12. Observability

### 12.1 Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| `voice.latency.v2v` | Voice-to-voice latency | < 1500ms (P95) |
| `voice.latency.stt` | Amazon Transcribe latency | < 400ms (P95) |
| `voice.latency.llm_ttft` | Bedrock time to first token | < 600ms (P95) |
| `voice.latency.tts` | Amazon Polly synthesis time | < 300ms (P95) |
| `session.count` | Active sessions | Dashboard |
| `session.errors` | Session error rate | < 1% |
| `aws.cost.daily` | Daily AWS AI service cost | Monitor |

### 12.2 Tracing Setup

```python
# apps/agent/src/config/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_tracing(service_name: str, enabled: bool = True) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Service name for traces.
        enabled: Whether tracing is enabled.
    """
    if not enabled:
        return

    provider = TracerProvider()
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
```

---

## 13. Security Considerations

### 13.1 Token Security
- Tokens have 10-minute TTL
- Tokens are generated server-side only
- API key/secret never exposed to client

### 13.2 AWS Security
- Use IAM roles with least privilege
- Credentials via environment variables only
- Enable CloudTrail for audit logging

### 13.3 Room Security
- Room names should be UUIDs or hashed
- No PII in room metadata
- Participant identity validated server-side

---

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LiveKit Cloud unavailable | High | Monitor status, implement retry logic |
| AWS service latency | Medium | Set timeouts, show "thinking" state |
| Amazon Transcribe JP accuracy | Medium | Custom vocabulary for domain terms |
| Browser audio permissions | Medium | Clear permission prompts, fallback UI |
| Network interruption | Medium | Auto-reconnect logic, state preservation |
| AWS cost overrun | Low | Set billing alerts, monitor usage |

---

## 15. References

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LiveKit AWS Integration](https://docs.livekit.io/agents/integrations/aws/)
- [Amazon Transcribe Japanese](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [Amazon Polly Japanese Voices](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html)
- [Amazon Bedrock Claude](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)
- [ADR-001: System Architecture](../adr/001-system-architecture.md)
- [EchoSphere Tech Stack](../architecture/tech-stack.md)
