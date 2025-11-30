import { http, HttpResponse, delay } from "msw";

import type {
  RecordingDetailResponse,
  RecordingListResponse,
  RecordingSummary,
  TranscriptMessage,
} from "@/features/recording-player/types";

// Default mock data
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
    content: "The recording feature captures your voice conversation with me in real-time.",
    timestampMs: 12000,
  },
];

const MOCK_RECORDINGS: RecordingSummary[] = [
  {
    id: "rec-001",
    sessionId: "sess-12345678",
    status: "completed",
    durationSeconds: 180,
    createdAt: new Date().toISOString(),
    playbackUrl: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
  },
  {
    id: "rec-002",
    sessionId: "sess-87654321",
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
];

// Helper to create recording list response
export function createMockRecordingListResponse(
  overrides: Partial<RecordingListResponse> = {}
): RecordingListResponse {
  return {
    recordings: MOCK_RECORDINGS,
    total: MOCK_RECORDINGS.length,
    page: 1,
    pageSize: 20,
    ...overrides,
  };
}

// Helper to create recording detail response
export function createMockRecordingDetail(
  id: string,
  overrides: Partial<RecordingDetailResponse> = {}
): RecordingDetailResponse {
  const foundRecording = MOCK_RECORDINGS.find((r) => r.id === id);
  const baseRecording = foundRecording ?? MOCK_RECORDINGS[0];

  // Default values if no recording found
  const recording = baseRecording ?? {
    id: "rec-default",
    sessionId: "sess-default",
    status: "completed" as const,
    durationSeconds: 120,
    createdAt: new Date().toISOString(),
    playbackUrl: null,
  };

  return {
    ...recording,
    id,
    fileSizeBytes: recording.durationSeconds ? recording.durationSeconds * 50000 : null,
    startedAt: new Date(Date.parse(recording.createdAt) - 5000).toISOString(),
    endedAt:
      recording.status === "completed"
        ? new Date(
            Date.parse(recording.createdAt) + (recording.durationSeconds || 0) * 1000
          ).toISOString()
        : null,
    transcript: recording.status === "completed" ? MOCK_TRANSCRIPT : [],
    ...overrides,
  };
}

// Default handlers
export const handlers = [
  // GET /api/recordings - List recordings with pagination
  http.get("/api/recordings", async ({ request }) => {
    const url = new URL(request.url);
    const page = Number.parseInt(url.searchParams.get("page") ?? "1", 10);
    const pageSize = Number.parseInt(url.searchParams.get("pageSize") ?? "20", 10);

    // Small delay to simulate network
    await delay(10);

    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedRecordings = MOCK_RECORDINGS.slice(start, end);

    return HttpResponse.json<RecordingListResponse>({
      recordings: paginatedRecordings,
      total: MOCK_RECORDINGS.length,
      page,
      pageSize,
    });
  }),

  // GET /api/recordings/:id - Get recording detail
  http.get("/api/recordings/:id", async ({ params }) => {
    const { id } = params;

    await delay(10);

    const recording = MOCK_RECORDINGS.find((r) => r.id === id);
    if (!recording) {
      return new HttpResponse(null, { status: 404 });
    }

    return HttpResponse.json<RecordingDetailResponse>(createMockRecordingDetail(id as string));
  }),
];
