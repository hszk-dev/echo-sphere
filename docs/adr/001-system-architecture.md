# ADR-001: System Architecture

**Status**: Accepted
**Date**: 2024-11-29
**Deciders**: Project Owner

## Context

EchoSphere is a real-time AI voice interaction platform with recording and playback capabilities, designed as an L5-level portfolio project. The system requires:

1. **Low-latency real-time communication**: Voice-to-voice AI interaction under 1 second
2. **Recording & archival**: Session capture with multiple participants
3. **Adaptive playback**: ABR streaming for optimal user experience
4. **Observability**: Comprehensive monitoring and evaluation of AI interactions

We need to select an architecture that supports these requirements while demonstrating senior engineering capabilities.

## Decision Drivers

- **Latency**: Real-time voice requires sub-second response times
- **Scalability**: Architecture should support horizontal scaling
- **Reliability**: Recording must not lose data on failures
- **Observability**: Full visibility into AI decision-making and performance
- **Developer Experience**: Clear separation of concerns for maintainability
- **Portfolio Value**: Demonstrate modern architecture patterns

## Considered Options

1. **Monolithic Architecture**: Single deployable unit
2. **Microservices Architecture**: Fully distributed services
3. **Pipeline-based Architecture**: Specialized pipelines with clear boundaries

## Decision Outcome

**Chosen Option**: Pipeline-based Architecture with three specialized pipelines

### Rationale

The pipeline-based approach provides:
- Clear separation between real-time (latency-critical) and batch (throughput-critical) workloads
- Ability to scale each pipeline independently
- Fault isolation between pipelines
- Simpler than full microservices while more scalable than monolith

### Consequences

**Positive:**
- Each pipeline can be optimized for its specific requirements
- Failures in media processing don't affect real-time interactions
- Clear mental model for developers and AI agents
- Demonstrates understanding of system trade-offs

**Negative:**
- More infrastructure to manage than monolith
- Need to design inter-pipeline communication carefully
- Increased complexity in local development setup

**Risks:**
- **Pipeline coupling**: Mitigated by using message queues for async communication
- **Consistency**: Mitigated by designing for eventual consistency where acceptable

## Architecture Overview

### Three Core Pipelines

```
┌─────────────────────────────────────────────────────────────────┐
│                        EchoSphere                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Pipeline 1: Real-time Interaction                 │   │
│  │  • Priority: Latency                                      │   │
│  │  • Tech: LiveKit, WebRTC, LiveKit Agents                 │   │
│  │  • Scale: Based on concurrent rooms                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ Events (Egress triggers)          │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Pipeline 2: Media Processing                      │   │
│  │  • Priority: Throughput, Reliability                      │   │
│  │  • Tech: S3, SQS, MediaConvert, CloudFront               │   │
│  │  • Scale: Based on queue depth                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ Metrics, Traces                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Pipeline 3: Intelligence & Observability          │   │
│  │  • Priority: Insights, Quality                            │   │
│  │  • Tech: OpenTelemetry, LangSmith, LLM Evaluation        │   │
│  │  • Scale: Based on session volume                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Backend (Python): Hexagonal Architecture

The AI agent backend follows Hexagonal Architecture (Ports & Adapters):

```
┌─────────────────────────────────────────────────────────┐
│                    Adapters (Inbound)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   LiveKit   │  │    HTTP     │  │    WebSocket    │ │
│  │   Worker    │  │   Handler   │  │    Handler      │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          ▼                              │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Use Cases / Services                │   │
│  │  • ProcessVoiceInteraction                       │   │
│  │  • EvaluateSession                               │   │
│  │  • ManageRecording                               │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│                        ▼                                │
├─────────────────────────────────────────────────────────┤
│                     Domain Layer                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Pure Business Logic                 │   │
│  │  • Entities (Session, Participant, Message)      │   │
│  │  • Value Objects (AudioBuffer, Transcript)       │   │
│  │  • Domain Services                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   Adapters (Outbound)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  OpenAI  │  │ Deepgram │  │ ElevenLabs│  │   S3   │ │
│  │ Adapter  │  │ Adapter  │  │  Adapter  │  │ Adapter│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Frontend (TypeScript): Feature-Sliced Design

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group
│   ├── room/[id]/         # Room pages
│   └── recordings/        # Recording pages
│
├── features/              # Feature modules
│   ├── voice-room/        # Real-time voice interaction
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api/
│   ├── recording-player/  # Playback feature
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api/
│   └── session-list/      # Session management
│
└── shared/                # Shared code
    ├── components/        # Reusable UI
    ├── hooks/             # Shared hooks
    ├── lib/               # Utilities
    └── types/             # Shared types
```

## Implementation Notes

### Phase 1: Core Voice Interaction
- Set up LiveKit Server (Cloud or self-hosted)
- Implement basic LiveKit Agent (STT → LLM → TTS)
- Build frontend voice room UI

### Phase 2: Recording & ABR Pipeline
- Configure LiveKit Egress for room composite
- Build S3 → SQS → MediaConvert → CloudFront pipeline
- Implement HLS player with ABR support

### Phase 3: Observability & Evaluation
- Integrate OpenTelemetry across all services
- Set up LangSmith for LLM observability
- Implement LLM-as-a-Judge evaluation

## References

- [LiveKit Architecture](https://docs.livekit.io/home/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Feature-Sliced Design](https://feature-sliced.design/)
- [HLS Specification](https://datatracker.ietf.org/doc/html/rfc8216)
