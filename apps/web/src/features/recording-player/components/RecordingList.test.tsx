import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/test/mocks/server";
import { render } from "@/test/utils";

import type { RecordingListResponse, RecordingSummary } from "../types";
import { RecordingList } from "./RecordingList";

// Mock the API module to bypass USE_MOCK_API and use actual fetch (intercepted by MSW)
vi.mock("../api/recordings", () => ({
  fetchRecordings: async (page = 1, pageSize = 20, signal?: AbortSignal) => {
    const response = await fetch(`/api/recordings?page=${page}&pageSize=${pageSize}`, { signal });
    if (!response.ok) {
      throw new Error(response.statusText || "Network error");
    }
    return response.json();
  },
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const createMockRecording = (overrides: Partial<RecordingSummary> = {}): RecordingSummary => ({
  id: `rec-${Math.random().toString(36).slice(2, 9)}`,
  sessionId: `session-${Math.random().toString(36).slice(2, 9)}`,
  status: "completed",
  durationSeconds: 120,
  createdAt: new Date().toISOString(),
  playbackUrl: "https://example.com/playlist.m3u8",
  ...overrides,
});

const createMockResponse = (
  recordings: RecordingSummary[],
  overrides: Partial<RecordingListResponse> = {}
): RecordingListResponse => ({
  recordings,
  total: recordings.length,
  page: 1,
  pageSize: 20,
  ...overrides,
});

// Helper to set up MSW handler for recordings list
const setupRecordingsHandler = (response: RecordingListResponse) => {
  server.use(
    http.get("/api/recordings", () => {
      return HttpResponse.json(response);
    })
  );
};

// Helper to set up MSW error handler
const setupErrorHandler = (status = 500, statusText = "Network error") => {
  server.use(
    http.get("/api/recordings", () => {
      return new HttpResponse(null, { status, statusText });
    })
  );
};

describe("RecordingList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("loading state", () => {
    it("shows loading spinner initially", () => {
      // Use a handler that never resolves
      server.use(
        http.get("/api/recordings", async () => {
          await new Promise(() => {}); // Never resolves
          return HttpResponse.json({});
        })
      );

      render(<RecordingList />);

      expect(screen.getByText("Loading recordings...")).toBeInTheDocument();
    });
  });

  describe("error state", () => {
    it("shows error message when fetch fails", async () => {
      setupErrorHandler(500, "Network error");

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("shows retry button on error", async () => {
      setupErrorHandler();

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Try Again" })).toBeInTheDocument();
      });
    });

    it("retries fetch when retry button clicked", async () => {
      const user = userEvent.setup();
      let callCount = 0;

      server.use(
        http.get("/api/recordings", () => {
          callCount++;
          if (callCount === 1) {
            return new HttpResponse("Network error", { status: 500 });
          }
          return HttpResponse.json(createMockResponse([createMockRecording()]));
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Try Again" })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Try Again" }));

      await waitFor(() => {
        expect(callCount).toBe(2);
      });
    });
  });

  describe("empty state", () => {
    it("shows empty state when no recordings", async () => {
      setupRecordingsHandler(createMockResponse([]));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("No recordings yet")).toBeInTheDocument();
      });
    });

    it("shows start session link in empty state", async () => {
      setupRecordingsHandler(createMockResponse([]));

      render(<RecordingList />);

      await waitFor(() => {
        const link = screen.getByRole("link", { name: /start session/i });
        expect(link).toHaveAttribute("href", "/");
      });
    });
  });

  describe("recording cards", () => {
    it("renders recording cards", async () => {
      const recordings = [
        createMockRecording({ sessionId: "session-12345678" }),
        createMockRecording({ sessionId: "session-87654321" }),
      ];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        // Should show last 8 chars of session ID
        expect(screen.getByText("Session 12345678")).toBeInTheDocument();
        expect(screen.getByText("Session 87654321")).toBeInTheDocument();
      });
    });

    it("shows play button for completed recordings", async () => {
      const recordings = [createMockRecording({ status: "completed", id: "rec-123" })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        const playLink = screen.getByRole("link", { name: /play/i });
        expect(playLink).toHaveAttribute("href", "/recordings/rec-123");
      });
    });

    it("shows unavailable text for non-completed recordings", async () => {
      const recordings = [createMockRecording({ status: "failed" })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("Unavailable")).toBeInTheDocument();
      });
    });

    it("shows processing text for processing recordings", async () => {
      const recordings = [createMockRecording({ status: "processing" })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("Processing...")).toBeInTheDocument();
      });
    });
  });

  describe("status badges", () => {
    const statusTests: { status: RecordingSummary["status"]; label: string }[] = [
      { status: "starting", label: "Starting" },
      { status: "active", label: "Recording" },
      { status: "processing", label: "Processing" },
      { status: "completed", label: "Ready" },
      { status: "failed", label: "Failed" },
    ];

    for (const { status, label } of statusTests) {
      it(`shows "${label}" badge for ${status} status`, async () => {
        const recordings = [createMockRecording({ status })];
        setupRecordingsHandler(createMockResponse(recordings));

        render(<RecordingList />);

        await waitFor(() => {
          expect(screen.getByText(label)).toBeInTheDocument();
        });
      });
    }
  });

  describe("duration formatting", () => {
    it("formats duration as MM:SS", async () => {
      const recordings = [createMockRecording({ durationSeconds: 125 })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("2:05")).toBeInTheDocument();
      });
    });

    it("shows --:-- for null duration", async () => {
      const recordings = [createMockRecording({ durationSeconds: null })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("--:--")).toBeInTheDocument();
      });
    });
  });

  describe("date formatting", () => {
    it("shows 'Just now' for very recent recordings", async () => {
      const recordings = [createMockRecording({ createdAt: new Date().toISOString() })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("Just now")).toBeInTheDocument();
      });
    });

    it("shows minutes ago for recent recordings", async () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      const recordings = [createMockRecording({ createdAt: fiveMinutesAgo.toISOString() })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("5m ago")).toBeInTheDocument();
      });
    });

    it("shows hours ago for recordings from today", async () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000);
      const recordings = [createMockRecording({ createdAt: threeHoursAgo.toISOString() })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("3h ago")).toBeInTheDocument();
      });
    });

    it("shows days ago for recordings from this week", async () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
      const recordings = [createMockRecording({ createdAt: twoDaysAgo.toISOString() })];
      setupRecordingsHandler(createMockResponse(recordings));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("2d ago")).toBeInTheDocument();
      });
    });
  });

  describe("pagination", () => {
    it("shows pagination when multiple pages exist", async () => {
      setupRecordingsHandler(
        createMockResponse([createMockRecording()], {
          total: 50,
          page: 1,
          pageSize: 20,
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
      });
    });

    it("disables previous button on first page", async () => {
      setupRecordingsHandler(
        createMockResponse([createMockRecording()], {
          total: 50,
          page: 1,
          pageSize: 20,
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        const prevButton = screen.getByRole("button", { name: "Previous" });
        expect(prevButton).toBeDisabled();
      });
    });

    it("enables next button when more pages exist", async () => {
      setupRecordingsHandler(
        createMockResponse([createMockRecording()], {
          total: 50,
          page: 1,
          pageSize: 20,
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        const nextButton = screen.getByRole("button", { name: "Next" });
        expect(nextButton).not.toBeDisabled();
      });
    });

    it("fetches next page when next button clicked", async () => {
      const user = userEvent.setup();
      let requestedPage = 1;

      server.use(
        http.get("/api/recordings", ({ request }) => {
          const url = new URL(request.url);
          requestedPage = Number.parseInt(url.searchParams.get("page") ?? "1", 10);
          return HttpResponse.json(
            createMockResponse([createMockRecording()], {
              total: 50,
              page: requestedPage,
              pageSize: 20,
            })
          );
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();
      });

      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(requestedPage).toBe(2);
      });
    });

    it("does not show pagination for single page", async () => {
      setupRecordingsHandler(
        createMockResponse([createMockRecording()], {
          total: 5,
          page: 1,
          pageSize: 20,
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.queryByText(/Page \d+ of \d+/)).not.toBeInTheDocument();
      });
    });
  });

  describe("refresh functionality", () => {
    it("shows refresh button", async () => {
      setupRecordingsHandler(createMockResponse([createMockRecording()]));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it("refetches data when refresh clicked", async () => {
      const user = userEvent.setup();
      let callCount = 0;

      server.use(
        http.get("/api/recordings", () => {
          callCount++;
          return HttpResponse.json(createMockResponse([createMockRecording()]));
        })
      );

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /refresh/i }));

      await waitFor(() => {
        expect(callCount).toBe(2);
      });
    });
  });

  describe("total count display", () => {
    it("shows total recording count", async () => {
      setupRecordingsHandler(createMockResponse([createMockRecording()], { total: 42 }));

      render(<RecordingList />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });
    });
  });

  describe("props", () => {
    it("uses initialPage prop", async () => {
      let requestedPage = 1;

      server.use(
        http.get("/api/recordings", ({ request }) => {
          const url = new URL(request.url);
          requestedPage = Number.parseInt(url.searchParams.get("page") ?? "1", 10);
          return HttpResponse.json(createMockResponse([createMockRecording()]));
        })
      );

      render(<RecordingList initialPage={3} />);

      await waitFor(() => {
        expect(requestedPage).toBe(3);
      });
    });

    it("uses pageSize prop", async () => {
      let requestedPageSize = 20;

      server.use(
        http.get("/api/recordings", ({ request }) => {
          const url = new URL(request.url);
          requestedPageSize = Number.parseInt(url.searchParams.get("pageSize") ?? "20", 10);
          return HttpResponse.json(createMockResponse([createMockRecording()]));
        })
      );

      render(<RecordingList pageSize={10} />);

      await waitFor(() => {
        expect(requestedPageSize).toBe(10);
      });
    });
  });
});
