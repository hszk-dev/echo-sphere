# EchoSphere - System Overview

## Vision

EchoSphere is a real-time AI voice interaction platform that provides:
- Low-latency voice conversations with AI
- Session recording and archival
- Adaptive bitrate playback
- Comprehensive observability and evaluation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EchoSphere Platform                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────────┐ │
│  │              │     │              │     │      Intelligence Pipeline       │ │
│  │   Frontend   │────▶│   LiveKit    │────▶│  ┌─────┐  ┌─────┐  ┌─────────┐  │ │
│  │   (Next.js)  │◀────│   Server     │◀────│  │ STT │─▶│ LLM │─▶│   TTS   │  │ │
│  │              │     │              │     │  └─────┘  └─────┘  └─────────┘  │ │
│  └──────────────┘     └──────┬───────┘     └──────────────────────────────────┘ │
│                              │                                                   │
│                              │ Egress                                           │
│                              ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        Media Processing Pipeline                          │  │
│  │                                                                            │  │
│  │  ┌─────────┐     ┌─────────┐     ┌────────────┐     ┌─────────────────┐  │  │
│  │  │ S3 Raw  │────▶│   SQS   │────▶│ Transcode  │────▶│  S3 Processed   │  │  │
│  │  │ Bucket  │     │  Queue  │     │ (MediaConvert)   │  (HLS Segments) │  │  │
│  │  └─────────┘     └─────────┘     └────────────┘     └────────┬────────┘  │  │
│  │                                                               │           │  │
│  └───────────────────────────────────────────────────────────────┼───────────┘  │
│                                                                  │              │
│                                                                  ▼              │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         Content Delivery                                   │  │
│  │                                                                            │  │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐  │  │
│  │  │  CloudFront │◀────│ HLS Player  │◀────│  Frontend (Playback Page)   │  │  │
│  │  │    (CDN)    │     │  (HLS.js)   │     │                             │  │  │
│  │  └─────────────┘     └─────────────┘     └─────────────────────────────┘  │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      Observability & Evaluation                           │  │
│  │                                                                            │  │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐  │  │
│  │  │ OpenTelemetry│────▶│  LangSmith  │     │    LLM-as-a-Judge          │  │  │
│  │  │   (Traces)  │     │  (LLM Obs)  │     │    (Evaluation)            │  │  │
│  │  └─────────────┘     └─────────────┘     └─────────────────────────────┘  │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Pipelines

### 1. Real-time Interaction Pipeline

**Purpose**: Enable low-latency voice conversations between users and AI.

**Components**:
- **LiveKit Server**: WebRTC media server for real-time audio/video
- **LiveKit Agents**: Python backend for AI logic orchestration
- **STT (Speech-to-Text)**: Convert user speech to text (Deepgram/Whisper)
- **LLM**: Generate AI responses (GPT-4o)
- **TTS (Text-to-Speech)**: Convert AI response to voice (ElevenLabs)

**Key Metrics**:
- Voice-to-Voice Latency: < 1 second target
- STT Latency: < 300ms
- LLM First Token: < 500ms
- TTS Latency: < 200ms

### 2. Media Processing Pipeline

**Purpose**: Record, transcode, and prepare sessions for playback.

**Flow**:
1. LiveKit Egress captures room composite (user + AI + screen share)
2. Raw MP4 uploaded to S3 (raw bucket)
3. S3 event triggers SQS message
4. Worker invokes MediaConvert for transcoding
5. HLS segments (multiple qualities) stored in processed bucket
6. CDN serves content with adaptive bitrate

**Renditions**:
| Quality | Resolution | Bitrate |
|---------|------------|---------|
| High    | 1080p      | 4.5 Mbps |
| Medium  | 720p       | 2.5 Mbps |
| Low     | 480p       | 1.0 Mbps |

### 3. Intelligence & Observability Pipeline

**Purpose**: Monitor, trace, and evaluate AI interactions.

**Components**:
- **OpenTelemetry**: Distributed tracing across all services
- **LangSmith**: LLM-specific observability (prompts, tokens, latency)
- **LLM-as-a-Judge**: Automated evaluation of conversation quality

**Evaluation Metrics**:
- Faithfulness (hallucination detection)
- User Sentiment
- Goal Completion
- Response Relevance

## Data Flow

### Real-time Session

```
User Browser                LiveKit                    AI Agent
    │                          │                          │
    │──── Join Room ──────────▶│                          │
    │◀─── Room Joined ─────────│                          │
    │                          │                          │
    │──── Audio Stream ───────▶│──── Audio Frames ───────▶│
    │                          │                          │
    │                          │                     ┌────┴────┐
    │                          │                     │   STT   │
    │                          │                     └────┬────┘
    │                          │                          │
    │                          │                     ┌────┴────┐
    │                          │                     │   LLM   │
    │                          │                     └────┬────┘
    │                          │                          │
    │                          │                     ┌────┴────┐
    │                          │                     │   TTS   │
    │                          │                     └────┬────┘
    │                          │                          │
    │◀─── AI Audio Stream ─────│◀─── Audio Response ──────│
    │                          │                          │
```

### Recording & Playback

```
LiveKit Egress          S3 Raw           Worker          S3 Processed       CDN
      │                   │                │                  │              │
      │─── Upload MP4 ───▶│                │                  │              │
      │                   │─── Event ─────▶│                  │              │
      │                   │                │─── Transcode ───▶│              │
      │                   │                │                  │─── Sync ────▶│
      │                   │                │                  │              │
                                                                             │
User Browser ◀───────────────────── HLS Stream ─────────────────────────────┘
```

## Security Considerations

- All API endpoints authenticated
- Presigned URLs for media access (time-limited)
- Room tokens with scoped permissions
- Secrets managed via environment variables
- No PII in logs

## Scalability Design

- **Horizontal**: LiveKit servers can scale based on room count
- **Async Processing**: Media transcoding decoupled via queue
- **CDN**: Global edge distribution for playback
- **Stateless Agents**: AI agents can scale independently

## Failure Modes

| Component | Failure Impact | Mitigation |
|-----------|---------------|------------|
| LiveKit Server | Session drops | Auto-reconnect, multiple servers |
| AI Agent | No AI response | Fallback message, retry logic |
| STT Service | No transcription | Queue audio, retry |
| Egress | Recording lost | Redundant egress, alerts |
| MediaConvert | No HLS | DLQ, manual retry |
