import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/test/mocks/server";
import { createMockRecordingDetail, render } from "@/test/utils";

import type { RecordingDetail, RecordingDetailResponse } from "../types";
import { PlaybackView } from "./PlaybackView";

// Mock the API module to bypass USE_MOCK_API and use actual fetch (intercepted by MSW)
vi.mock("../api/recordings", () => ({
  fetchRecordingDetail: async (id: string, signal?: AbortSignal) => {
    const response = await fetch(`/api/recordings/${id}`, { signal });
    if (!response.ok) {
      throw new Error(response.statusText || "Network error");
    }
    return response.json();
  },
}));

// Helper to set up MSW handler for recording detail
const setupRecordingDetailHandler = (recording: RecordingDetailResponse) => {
  server.use(
    http.get("/api/recordings/:id", () => {
      return HttpResponse.json(recording);
    })
  );
};

// Helper to set up MSW error handler
const setupErrorHandler = (status = 404, message = "Not found") => {
  server.use(
    http.get("/api/recordings/:id", () => {
      return new HttpResponse(message, { status, statusText: message });
    })
  );
};

// Helper to set up never-resolving handler (for loading state)
const setupPendingHandler = () => {
  server.use(
    http.get("/api/recordings/:id", async () => {
      await new Promise(() => {}); // Never resolves
      return HttpResponse.json({});
    })
  );
};

// Mock child components to isolate PlaybackView tests
vi.mock("./VideoPlayer", () => ({
  // biome-ignore lint/style/useNamingConvention: Component name must match export
  VideoPlayer: ({
    src,
    onTimeUpdate,
    onError,
    className,
  }: {
    src: string | null;
    onTimeUpdate?: (time: number) => void;
    onError?: (error: Error) => void;
    className?: string;
  }) => (
    <div data-testid="video-player" data-src={src} className={className}>
      <button type="button" onClick={() => onTimeUpdate?.(5000)} data-testid="time-update-trigger">
        Trigger Time Update
      </button>
      <button
        type="button"
        onClick={() => onError?.(new Error("Test error"))}
        data-testid="error-trigger"
      >
        Trigger Error
      </button>
    </div>
  ),
}));

vi.mock("./SyncedTranscript", () => ({
  // biome-ignore lint/style/useNamingConvention: Component name must match export
  SyncedTranscript: ({
    transcript,
    currentTimeMs,
    onSeek,
    className,
  }: {
    transcript: unknown[];
    currentTimeMs: number;
    onSeek?: (time: number) => void;
    className?: string;
  }) => (
    <div
      data-testid="synced-transcript"
      data-current-time={currentTimeMs}
      data-transcript-count={transcript.length}
      className={className}
    >
      <button type="button" onClick={() => onSeek?.(3000)} data-testid="seek-trigger">
        Trigger Seek
      </button>
    </div>
  ),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("PlaybackView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("loading state", () => {
    it("shows loading spinner while fetching", () => {
      setupPendingHandler();

      render(<PlaybackView recordingId="test-id" />);

      expect(screen.getByText("Loading recording...")).toBeInTheDocument();
    });
  });

  describe("error state", () => {
    it("shows error message when fetch fails", async () => {
      setupErrorHandler(404, "Not found");

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("Not found")).toBeInTheDocument();
      });
    });

    it("shows back to recordings link on error", async () => {
      setupErrorHandler(404, "Not found");

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        const link = screen.getByRole("link", { name: /back to recordings/i });
        expect(link).toHaveAttribute("href", "/recordings");
      });
    });
  });

  describe("completed recording", () => {
    const completedRecording = createMockRecordingDetail({
      id: "test-id",
      sessionId: "session-12345678",
      status: "completed",
      playbackUrl: "https://example.com/video.m3u8",
      durationSeconds: 125,
      fileSizeBytes: 52428800, // 50 MB
      transcript: [
        { id: "1", role: "user", content: "Hello", timestampMs: 0 },
        { id: "2", role: "assistant", content: "Hi", timestampMs: 1000 },
      ],
    });

    it("renders video player for completed recording", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByTestId("video-player")).toBeInTheDocument();
      });
    });

    it("passes playback URL to video player", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        const player = screen.getByTestId("video-player");
        expect(player).toHaveAttribute("data-src", "https://example.com/video.m3u8");
      });
    });

    it("renders synced transcript", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        const transcript = screen.getByTestId("synced-transcript");
        expect(transcript).toHaveAttribute("data-transcript-count", "2");
      });
    });

    it("shows session ID in header", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("Session 12345678")).toBeInTheDocument();
      });
    });

    it("shows back button", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        const link = screen.getByRole("link", { name: /back to recordings/i });
        expect(link).toHaveAttribute("href", "/recordings");
      });
    });

    it("shows Ready to Play status badge", async () => {
      setupRecordingDetailHandler(completedRecording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("Ready to Play")).toBeInTheDocument();
      });
    });
  });

  describe("recording stats", () => {
    it("shows formatted duration", async () => {
      const recording = createMockRecordingDetail({
        status: "completed",
        playbackUrl: "https://example.com/video.m3u8",
        durationSeconds: 125,
      });
      setupRecordingDetailHandler(recording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("2:05")).toBeInTheDocument();
      });
    });

    it("shows formatted file size", async () => {
      const recording = createMockRecordingDetail({
        status: "completed",
        playbackUrl: "https://example.com/video.m3u8",
        fileSizeBytes: 52428800, // 50 MB
      });
      setupRecordingDetailHandler(recording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("50.0 MB")).toBeInTheDocument();
      });
    });

    it("shows message count", async () => {
      const recording = createMockRecordingDetail({
        status: "completed",
        playbackUrl: "https://example.com/video.m3u8",
        transcript: [
          { id: "1", role: "user", content: "Hello", timestampMs: 0 },
          { id: "2", role: "assistant", content: "Hi", timestampMs: 1000 },
          { id: "3", role: "user", content: "Bye", timestampMs: 2000 },
        ],
      });
      setupRecordingDetailHandler(recording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.getByText("3")).toBeInTheDocument();
      });
    });
  });

  describe("non-playable states", () => {
    const nonPlayableTests: {
      status: RecordingDetail["status"];
      message: string;
    }[] = [
      { status: "processing", message: "Recording is being processed" },
      { status: "active", message: "Recording in progress" },
      { status: "starting", message: "Recording is starting" },
      { status: "failed", message: "Recording unavailable" },
    ];

    for (const { status, message } of nonPlayableTests) {
      it(`shows "${message}" for ${status} status`, async () => {
        const recording = createMockRecordingDetail({
          status,
          playbackUrl: null,
        });
        setupRecordingDetailHandler(recording);

        render(<PlaybackView recordingId="test-id" />);

        await waitFor(() => {
          expect(screen.getByText(message)).toBeInTheDocument();
        });
      });
    }

    it("does not render video player for non-playable recording", async () => {
      const recording = createMockRecordingDetail({
        status: "processing",
        playbackUrl: null,
      });
      setupRecordingDetailHandler(recording);

      render(<PlaybackView recordingId="test-id" />);

      await waitFor(() => {
        expect(screen.queryByTestId("video-player")).not.toBeInTheDocument();
      });
    });
  });

  describe("status badges", () => {
    const statusTests: {
      status: RecordingDetail["status"];
      label: string;
    }[] = [
      { status: "starting", label: "Starting" },
      { status: "active", label: "Recording in Progress" },
      { status: "processing", label: "Processing" },
      { status: "completed", label: "Ready to Play" },
      { status: "failed", label: "Failed" },
    ];

    for (const { status, label } of statusTests) {
      it(`shows "${label}" badge for ${status} status`, async () => {
        const recording = createMockRecordingDetail({ status });
        setupRecordingDetailHandler(recording);

        render(<PlaybackView recordingId="test-id" />);

        await waitFor(() => {
          expect(screen.getByText(label)).toBeInTheDocument();
        });
      });
    }
  });

  describe("format functions", () => {
    describe("formatFileSize", () => {
      it("shows -- for null", async () => {
        const recording = createMockRecordingDetail({
          status: "completed",
          playbackUrl: "https://example.com/video.m3u8",
          fileSizeBytes: null,
        });
        setupRecordingDetailHandler(recording);

        render(<PlaybackView recordingId="test-id" />);

        await waitFor(() => {
          expect(screen.getByText("--")).toBeInTheDocument();
        });
      });

      it("shows KB for small files", async () => {
        const recording = createMockRecordingDetail({
          status: "completed",
          playbackUrl: "https://example.com/video.m3u8",
          fileSizeBytes: 5120, // 5 KB
        });
        setupRecordingDetailHandler(recording);

        render(<PlaybackView recordingId="test-id" />);

        await waitFor(() => {
          expect(screen.getByText("5.0 KB")).toBeInTheDocument();
        });
      });
    });

    describe("formatDuration", () => {
      it("shows --:-- for null", async () => {
        const recording = createMockRecordingDetail({
          status: "completed",
          playbackUrl: "https://example.com/video.m3u8",
          durationSeconds: null,
        });
        setupRecordingDetailHandler(recording);

        render(<PlaybackView recordingId="test-id" />);

        await waitFor(() => {
          expect(screen.getByText("--:--")).toBeInTheDocument();
        });
      });
    });
  });

  describe("re-fetch on recordingId change", () => {
    it("fetches new recording when recordingId changes", async () => {
      const requestedIds: string[] = [];

      server.use(
        http.get("/api/recordings/:id", ({ params }) => {
          requestedIds.push(params.id as string);
          const recording = createMockRecordingDetail({
            id: params.id as string,
            status: "completed",
          });
          return HttpResponse.json(recording);
        })
      );

      const { rerender } = render(<PlaybackView recordingId="id-1" />);

      await waitFor(() => {
        expect(requestedIds).toContain("id-1");
      });

      // Change recordingId
      rerender(<PlaybackView recordingId="id-2" />);

      await waitFor(() => {
        expect(requestedIds).toContain("id-2");
      });
    });
  });
});
