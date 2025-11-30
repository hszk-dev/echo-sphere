import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { server } from "./mocks/server";

// MSW server lifecycle
beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// HLS.js Events and ErrorTypes constants (mirroring HLS.js API)
const HlsEvents = {
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  MANIFEST_PARSED: "hlsManifestParsed",
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  ERROR: "hlsError",
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  LEVEL_LOADED: "hlsLevelLoaded",
} as const;

const HlsErrorTypes = {
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  NETWORK_ERROR: "networkError",
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  MEDIA_ERROR: "mediaError",
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
  OTHER_ERROR: "otherError",
} as const;

// Shared mock HLS instance for test inspection
const mockHlsInstance = {
  loadSource: vi.fn(),
  attachMedia: vi.fn(),
  destroy: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  recoverMediaError: vi.fn(),
  startLoad: vi.fn(),
};

// Mock HLS.js constructor function with static properties
const MockHls = Object.assign(
  vi.fn(() => mockHlsInstance),
  {
    isSupported: vi.fn(() => true),
    // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
    Events: HlsEvents,
    // biome-ignore lint/style/useNamingConvention: Matches HLS.js API
    ErrorTypes: HlsErrorTypes,
  }
);

vi.mock("hls.js", () => ({
  default: MockHls,
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js export names
  Events: HlsEvents,
  // biome-ignore lint/style/useNamingConvention: Matches HLS.js export names
  ErrorTypes: HlsErrorTypes,
}));

export { mockHlsInstance, MockHls };

// Mock matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: MockResizeObserver,
});

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();
