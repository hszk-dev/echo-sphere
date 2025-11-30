import { type RenderOptions, render } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";

import type {
  RecordingDetail,
  RecordingSummary,
  TranscriptMessage,
} from "@/features/recording-player/types";

// Add providers here if needed (e.g., context providers)
function AllProviders({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) =>
  render(ui, { wrapper: AllProviders, ...options });

// Re-export everything
export * from "@testing-library/react";
export { customRender as render };

// ============================================
// Mock Data Factories
// ============================================

export const createMockTranscriptMessage = (
  overrides: Partial<TranscriptMessage> = {}
): TranscriptMessage => ({
  id: `msg-${Math.random().toString(36).slice(2, 9)}`,
  role: "user",
  content: "Test message",
  timestampMs: 0,
  ...overrides,
});

export const createMockTranscript = (count = 4): TranscriptMessage[] => [
  createMockTranscriptMessage({
    id: "1",
    role: "user",
    content: "Hello, how are you?",
    timestampMs: 0,
  }),
  createMockTranscriptMessage({
    id: "2",
    role: "assistant",
    content: "I'm doing well, thank you for asking!",
    timestampMs: 2000,
  }),
  ...(count > 2
    ? [
        createMockTranscriptMessage({
          id: "3",
          role: "user",
          content: "Can you help me with something?",
          timestampMs: 5000,
        }),
        createMockTranscriptMessage({
          id: "4",
          role: "assistant",
          content: "Of course! What do you need help with?",
          timestampMs: 7500,
        }),
      ]
    : []),
];

export const createMockRecordingSummary = (
  overrides: Partial<RecordingSummary> = {}
): RecordingSummary => ({
  id: `rec-${Math.random().toString(36).slice(2, 9)}`,
  sessionId: `session-${Math.random().toString(36).slice(2, 9)}`,
  status: "completed",
  durationSeconds: 120,
  createdAt: new Date().toISOString(),
  playbackUrl: "https://example.com/playlist.m3u8",
  ...overrides,
});

export const createMockRecordingDetail = (
  overrides: Partial<RecordingDetail> = {}
): RecordingDetail => ({
  ...createMockRecordingSummary(),
  fileSizeBytes: 1024 * 1024 * 50, // 50 MB
  startedAt: new Date(Date.now() - 120000).toISOString(),
  endedAt: new Date().toISOString(),
  transcript: createMockTranscript(),
  ...overrides,
});

// ============================================
// Test Helpers
// ============================================

/**
 * Wait for a condition to be true
 */
export const waitForCondition = async (condition: () => boolean, timeout = 1000): Promise<void> => {
  const startTime = Date.now();
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error("Timeout waiting for condition");
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
};

/**
 * Create a mock video element for testing
 */
export const createMockVideoElement = () => {
  const element = document.createElement("video");

  // Add properties that tests might check
  Object.defineProperties(element, {
    currentTime: {
      get: () => 0,
      set: vi.fn(),
      configurable: true,
    },
    duration: {
      value: 120,
      configurable: true,
    },
    paused: {
      value: true,
      configurable: true,
    },
    volume: {
      get: () => 1,
      set: vi.fn(),
      configurable: true,
    },
    muted: {
      get: () => false,
      set: vi.fn(),
      configurable: true,
    },
  });

  element.play = vi.fn().mockResolvedValue(undefined);
  element.pause = vi.fn();
  element.load = vi.fn();

  return element;
};
