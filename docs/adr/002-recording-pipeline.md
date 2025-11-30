# ADR-002: Recording Pipeline Architecture

**Status**: Accepted
**Date**: 2024-11-30
**Deciders**: Project Owner

## Context

EchoSphere requires recording and playback functionality for voice AI sessions. Users need to:
1. Record their voice interactions with the AI
2. Replay past sessions with synchronized transcript
3. Access recordings from any device with adaptive quality

The recording system must integrate with the existing LiveKit-based real-time voice interaction pipeline established in Phase 1.

## Decision Drivers

- **Simplicity**: Minimize infrastructure complexity for MVP
- **Cost-effectiveness**: Avoid expensive transcoding services where possible
- **Time-to-playback**: Recordings should be available immediately after session ends
- **User Experience**: Smooth playback with synchronized transcript
- **Scalability**: Architecture should support future ABR enhancement

## Considered Options

1. **Option A: Direct HLS from LiveKit**
   - LiveKit Egress → HLS Segments → S3 → CDN
   - Single quality output directly from LiveKit

2. **Option B: Full ABR Pipeline**
   - LiveKit Egress → MP4 → AWS MediaConvert → Multi-bitrate HLS → CloudFront
   - True adaptive bitrate with multiple renditions (1080p/720p/480p)

3. **Option C: Hybrid Approach**
   - Immediate: LiveKit → HLS (single quality) for fast access
   - Async: Background job → MediaConvert → ABR versions later

## Decision Outcome

**Chosen Option**: Option A - Direct HLS from LiveKit

### Rationale

1. **LiveKit Egress Capability**: LiveKit Egress can output HLS segments directly to S3, eliminating the need for external transcoding services.

2. **Voice AI Focus**: EchoSphere sessions are primarily audio-focused with minimal video (AI avatar). Single quality is sufficient for audio-heavy content.

3. **Cost Optimization**: No AWS MediaConvert costs (~$0.015/minute saved per recording).

4. **Immediate Availability**: Recordings are playable immediately after session ends, no transcoding delay.

5. **Future Extensibility**: Can add Option B or C in Phase 3 if user demand for ABR increases.

### Consequences

**Positive:**
- Simplified architecture with fewer moving parts
- Lower operational costs
- Faster time-to-playback
- Easier debugging and maintenance

**Negative:**
- No true ABR (adaptive bitrate) - users on slow connections get the same quality
- Single point of failure (LiveKit Egress)

**Risks:**
- **Egress Reliability**: Mitigated by monitoring egress status via webhooks and implementing retry logic
- **Storage Costs**: Mitigated by 30-day retention policy with S3 Lifecycle

## Options Analysis

### Option A: Direct HLS from LiveKit

**Description**: Use LiveKit's built-in Egress service to output HLS segments directly to S3-compatible storage (MinIO for development, S3 for production).

**Architecture**:
```
LiveKit Server
      │
      ▼
LiveKit Egress (RoomComposite)
      │
      ├── HLS Segments (.ts)
      └── Playlist (.m3u8)
            │
            ▼
      S3 / MinIO
            │
            ▼
      Presigned URLs
            │
            ▼
      HLS.js Player
```

**Pros:**
- Native LiveKit integration
- No additional services required
- Real-time segment upload during recording
- Built-in layout templates

**Cons:**
- Single quality output
- Depends on LiveKit Egress availability
- Limited customization of output format

### Option B: Full ABR Pipeline

**Description**: Record raw MP4 via LiveKit Egress, then use AWS MediaConvert to generate multi-bitrate HLS with CloudFront distribution.

**Architecture**:
```
LiveKit Egress → MP4 → S3 (Raw)
                        │
                        ▼
                  SQS Queue
                        │
                        ▼
              AWS MediaConvert
                        │
                        ├── 1080p (4.5 Mbps)
                        ├── 720p (2.5 Mbps)
                        └── 480p (1.0 Mbps)
                              │
                              ▼
                      S3 (Processed)
                              │
                              ▼
                        CloudFront
```

**Pros:**
- True ABR for optimal quality per bandwidth
- Industry-standard delivery via CloudFront
- Support for large-scale distribution

**Cons:**
- Higher complexity (SQS, Lambda, MediaConvert)
- Additional cost (~$0.015/minute)
- Delay before playback (transcoding time)
- More infrastructure to manage

### Option C: Hybrid Approach

**Description**: Combine Option A for immediate access with async Option B processing for eventual ABR availability.

**Pros:**
- Best of both worlds
- Immediate playback + eventual quality improvement

**Cons:**
- Most complex to implement
- Higher storage costs (two copies)
- Complex state management

## Implementation Notes

### Recording Lifecycle

```
Session Start
    │
    ├── Create Recording entity (status: STARTING)
    ├── Call LiveKit Egress API
    │       └── RoomCompositeEgress with SegmentedFileOutput
    │
    ▼
Recording Active
    │
    ├── Segments uploaded to S3 in real-time
    ├── Recording status: ACTIVE
    │
    ▼
Session End
    │
    ├── Stop Egress via API
    ├── Wait for egress_ended webhook
    ├── Recording status: PROCESSING → COMPLETED
    │
    ▼
Playback Available
```

### Key Configuration

```python
# Egress Output Configuration
SegmentedFileOutput(
    filename_prefix=f"recordings/{session_id}/",
    playlist_name="playlist.m3u8",
    segment_duration=4,  # seconds
    s3=S3Upload(
        bucket="echosphere-recordings",
        region="ap-northeast-1",
        access_key=settings.s3_access_key,
        secret=settings.s3_secret_key,
    )
)
```

### Storage Retention Policy

| Age | Storage Class | Action |
|-----|---------------|--------|
| 0-30 days | S3 Standard | Active storage |
| 30+ days | Deleted | S3 Lifecycle rule |

Future enhancement: Archive to S3 Glacier before deletion.

## References

- [LiveKit Egress Documentation](https://docs.livekit.io/home/egress/overview/)
- [LiveKit Egress Output Options](https://docs.livekit.io/home/egress/outputs/)
- [HLS Specification (RFC 8216)](https://datatracker.ietf.org/doc/html/rfc8216)
- [ADR-001: System Architecture](./001-system-architecture.md)
