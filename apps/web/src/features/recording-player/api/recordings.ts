import type {
  RecordingDetailResponse,
  RecordingListResponse,
  RecordingSummary,
  TranscriptMessage,
} from "../types";

// Mock data for development before API is ready
const MOCK_TRANSCRIPT: TranscriptMessage[] = [
  { id: "1", role: "user", content: "Hello, can you help me?", timestampMs: 1500 },
  {
    id: "2",
    role: "assistant",
    content: "Of course! I'd be happy to help. What do you need assistance with?",
    timestampMs: 4200,
  },
  {
    id: "3",
    role: "user",
    content: "I'm trying to understand how this recording feature works.",
    timestampMs: 8500,
  },
  {
    id: "4",
    role: "assistant",
    content:
      "The recording feature captures your voice conversation with me in real-time. Once completed, you can replay the session and see the transcript synchronized with the audio.",
    timestampMs: 12000,
  },
  {
    id: "5",
    role: "user",
    content: "That's really useful! Can I skip to specific parts?",
    timestampMs: 18500,
  },
  {
    id: "6",
    role: "assistant",
    content:
      "Yes! You can click on any transcript message to jump to that moment in the recording. The current message is highlighted as the playback progresses.",
    timestampMs: 22000,
  },
];

const MOCK_RECORDINGS: RecordingSummary[] = [
  {
    id: "rec-001",
    sessionId: "sess-001",
    status: "completed",
    durationSeconds: 180,
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    playbackUrl: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
  },
  {
    id: "rec-002",
    sessionId: "sess-002",
    status: "completed",
    durationSeconds: 245,
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    playbackUrl: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
  },
  {
    id: "rec-003",
    sessionId: "sess-003",
    status: "processing",
    durationSeconds: null,
    createdAt: new Date(Date.now() - 1800000).toISOString(),
    playbackUrl: null,
  },
  {
    id: "rec-004",
    sessionId: "sess-004",
    status: "active",
    durationSeconds: null,
    createdAt: new Date(Date.now() - 600000).toISOString(),
    playbackUrl: null,
  },
  {
    id: "rec-005",
    sessionId: "sess-005",
    status: "failed",
    durationSeconds: null,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    playbackUrl: null,
  },
];

// Flag to switch between mock and real API
const USE_MOCK_API = true;

// API base URL (will be set via environment variable in production)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

/**
 * Fetch list of recordings with pagination
 */
export async function fetchRecordings(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal
): Promise<RecordingListResponse> {
  if (USE_MOCK_API) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedRecordings = MOCK_RECORDINGS.slice(start, end);

    return {
      recordings: paginatedRecordings,
      total: MOCK_RECORDINGS.length,
      page,
      pageSize,
    };
  }

  const response = await fetch(`${API_BASE_URL}/recordings?page=${page}&pageSize=${pageSize}`, {
    signal,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch recordings: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch recording detail with transcript
 */
export async function fetchRecordingDetail(
  id: string,
  signal?: AbortSignal
): Promise<RecordingDetailResponse> {
  if (USE_MOCK_API) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 300));

    const recording = MOCK_RECORDINGS.find((r) => r.id === id);
    if (!recording) {
      throw new Error(`Recording not found: ${id}`);
    }

    return {
      ...recording,
      fileSizeBytes: recording.durationSeconds ? recording.durationSeconds * 50000 : null,
      startedAt: new Date(Date.parse(recording.createdAt) - 5000).toISOString(),
      endedAt:
        recording.status === "completed"
          ? new Date(
              Date.parse(recording.createdAt) + (recording.durationSeconds || 0) * 1000
            ).toISOString()
          : null,
      transcript: recording.status === "completed" ? MOCK_TRANSCRIPT : [],
    };
  }

  const response = await fetch(`${API_BASE_URL}/recordings/${id}`, { signal });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Recording not found: ${id}`);
    }
    throw new Error(`Failed to fetch recording: ${response.statusText}`);
  }

  return response.json();
}
