import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { render } from "@/test/utils";

import { VideoPlayer } from "./VideoPlayer";

// Mock useHlsPlayer hook
const mockControls = {
  play: vi.fn().mockResolvedValue(undefined),
  pause: vi.fn(),
  seek: vi.fn(),
  setVolume: vi.fn(),
};

const mockState = {
  isLoading: false,
  isReady: true,
  isPlaying: false,
  currentTime: 0,
  duration: 120,
  error: null as Error | null,
};

const mockVideoRef = { current: null as HTMLVideoElement | null };

vi.mock("../hooks/useHlsPlayer", () => ({
  useHlsPlayer: () => ({
    videoRef: mockVideoRef,
    state: mockState,
    controls: mockControls,
  }),
}));

describe("VideoPlayer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock state
    mockState.isLoading = false;
    mockState.isReady = true;
    mockState.isPlaying = false;
    mockState.currentTime = 0;
    mockState.duration = 120;
    mockState.error = null;
    mockVideoRef.current = null;
  });

  describe("empty state", () => {
    it("renders placeholder when no src provided", () => {
      render(<VideoPlayer src={null} />);

      expect(screen.getByText("No video source available")).toBeInTheDocument();
    });

    it("does not render video element when no src", () => {
      render(<VideoPlayer src={null} />);

      expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("shows loading overlay when isLoading is true", () => {
      mockState.isLoading = true;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });
  });

  describe("error state", () => {
    it("shows error overlay when error exists", () => {
      mockState.error = new Error("Test error message");

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("Playback Error")).toBeInTheDocument();
      expect(screen.getByText("Test error message")).toBeInTheDocument();
    });
  });

  describe("time formatting", () => {
    it("formats 0 seconds as 0:00", () => {
      mockState.currentTime = 0;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("0:00")).toBeInTheDocument();
    });

    it("formats 65 seconds as 1:05", () => {
      mockState.currentTime = 65;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("1:05")).toBeInTheDocument();
    });

    it("formats duration correctly", () => {
      mockState.currentTime = 0;
      mockState.duration = 125;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("2:05")).toBeInTheDocument();
    });
  });

  describe("callbacks", () => {
    it("calls onTimeUpdate with time in milliseconds", async () => {
      const onTimeUpdate = vi.fn();
      mockState.currentTime = 30;

      render(<VideoPlayer src="https://example.com/video.m3u8" onTimeUpdate={onTimeUpdate} />);

      await waitFor(() => {
        expect(onTimeUpdate).toHaveBeenCalledWith(30000); // 30 seconds = 30000 ms
      });
    });

    it("calls onDurationChange with duration in milliseconds", async () => {
      const onDurationChange = vi.fn();
      mockState.duration = 120;

      render(
        <VideoPlayer src="https://example.com/video.m3u8" onDurationChange={onDurationChange} />
      );

      await waitFor(() => {
        expect(onDurationChange).toHaveBeenCalledWith(120000); // 120 seconds = 120000 ms
      });
    });

    it("calls onError when error occurs", async () => {
      const onError = vi.fn();
      const error = new Error("Test error");
      mockState.error = error;

      render(<VideoPlayer src="https://example.com/video.m3u8" onError={onError} />);

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(error);
      });
    });
  });

  describe("playback controls", () => {
    it("calls play when clicking overlay while paused", async () => {
      const user = userEvent.setup();
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      // Click the first play button (overlay)
      const playButtons = screen.getAllByRole("button", { name: "Play" });
      const playButton = playButtons[0];
      if (!playButton) {
        throw new Error("Expected play button");
      }
      await user.click(playButton);

      expect(mockControls.play).toHaveBeenCalled();
    });

    it("calls pause when clicking overlay while playing", async () => {
      const user = userEvent.setup();
      mockState.isPlaying = true;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      // Click the first pause button (overlay)
      const pauseButtons = screen.getAllByRole("button", { name: "Pause" });
      const pauseButton = pauseButtons[0];
      if (!pauseButton) {
        throw new Error("Expected pause button");
      }
      await user.click(pauseButton);

      expect(mockControls.pause).toHaveBeenCalled();
    });

    it("shows play buttons when paused", () => {
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      // Should have play buttons visible (overlay + control bar)
      expect(screen.getAllByRole("button", { name: "Play" })).toHaveLength(2);
    });
  });

  describe("progress bar", () => {
    it("renders progress bar with correct aria attributes", () => {
      mockState.currentTime = 30;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      const slider = screen.getByRole("slider", { name: "Video progress" });
      expect(slider).toHaveAttribute("aria-valuemin", "0");
      expect(slider).toHaveAttribute("aria-valuemax", "100");
      expect(slider).toHaveAttribute("aria-valuenow", "25"); // 30/120 = 25%
    });

    it("calls seek when progress bar is clicked", () => {
      mockState.currentTime = 0;
      mockState.duration = 100;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      const slider = screen.getByRole("slider", { name: "Video progress" });

      // Mock getBoundingClientRect
      slider.getBoundingClientRect = vi.fn().mockReturnValue({
        left: 0,
        width: 100,
        top: 0,
        right: 100,
        bottom: 10,
        height: 10,
      });

      // Click at 50% position
      fireEvent.click(slider, { clientX: 50 });

      expect(mockControls.seek).toHaveBeenCalledWith(50); // 50% of 100 seconds
    });

    it("seeks backward on ArrowLeft keydown", () => {
      mockState.currentTime = 50;
      mockState.duration = 100;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      const slider = screen.getByRole("slider", { name: "Video progress" });
      fireEvent.keyDown(slider, { key: "ArrowLeft" });

      // Should seek back 5% (5 seconds for 100s duration)
      expect(mockControls.seek).toHaveBeenCalledWith(45);
    });

    it("seeks forward on ArrowRight keydown", () => {
      mockState.currentTime = 50;
      mockState.duration = 100;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      const slider = screen.getByRole("slider", { name: "Video progress" });
      fireEvent.keyDown(slider, { key: "ArrowRight" });

      // Should seek forward 5% (5 seconds for 100s duration)
      expect(mockControls.seek).toHaveBeenCalledWith(55);
    });
  });

  describe("keyboard shortcuts", () => {
    it("space toggles playback", () => {
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: " " });

      expect(mockControls.play).toHaveBeenCalled();
    });

    it("k toggles playback", () => {
      mockState.isPlaying = true;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "k" });

      expect(mockControls.pause).toHaveBeenCalled();
    });

    it("ArrowLeft seeks backward 5 seconds", () => {
      mockState.currentTime = 30;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "ArrowLeft" });

      expect(mockControls.seek).toHaveBeenCalledWith(25); // 30 - 5
    });

    it("j seeks backward 5 seconds", () => {
      mockState.currentTime = 30;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "j" });

      expect(mockControls.seek).toHaveBeenCalledWith(25);
    });

    it("ArrowRight seeks forward 5 seconds", () => {
      mockState.currentTime = 30;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "ArrowRight" });

      expect(mockControls.seek).toHaveBeenCalledWith(35); // 30 + 5
    });

    it("l seeks forward 5 seconds", () => {
      mockState.currentTime = 30;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "l" });

      expect(mockControls.seek).toHaveBeenCalledWith(35);
    });

    it("does not seek below 0", () => {
      mockState.currentTime = 2;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "ArrowLeft" });

      expect(mockControls.seek).toHaveBeenCalledWith(0);
    });

    it("does not seek above duration", () => {
      mockState.currentTime = 118;
      mockState.duration = 120;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      fireEvent.keyDown(window, { key: "ArrowRight" });

      expect(mockControls.seek).toHaveBeenCalledWith(120);
    });

    it("ignores keyboard shortcuts when typing in input", () => {
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      // Create and append an input element
      const input = document.createElement("input");
      document.body.appendChild(input);
      input.focus();

      // Simulate keydown on the input
      fireEvent.keyDown(input, { key: " " });

      expect(mockControls.play).not.toHaveBeenCalled();

      // Cleanup
      document.body.removeChild(input);
    });
  });

  describe("className prop", () => {
    it("applies custom className", () => {
      const { container } = render(
        <VideoPlayer src="https://example.com/video.m3u8" className="custom-class" />
      );

      expect(container.firstChild).toHaveClass("custom-class");
    });

    it("applies custom className to empty state", () => {
      const { container } = render(<VideoPlayer src={null} className="custom-class" />);

      expect(container.firstChild).toHaveClass("custom-class");
    });
  });

  describe("playback state visibility", () => {
    it("shows play controls when paused and ready", () => {
      mockState.isPlaying = false;
      mockState.isLoading = false;
      mockState.error = null;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      // Should have play buttons visible
      expect(screen.getAllByRole("button", { name: "Play" }).length).toBeGreaterThan(0);
    });

    it("shows pause controls when playing", () => {
      mockState.isPlaying = true;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getAllByRole("button", { name: "Pause" }).length).toBeGreaterThan(0);
    });

    it("shows loading overlay instead of play controls when loading", () => {
      mockState.isLoading = true;
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });

    it("shows error overlay instead of play controls on error", () => {
      mockState.error = new Error("Test error");
      mockState.isPlaying = false;

      render(<VideoPlayer src="https://example.com/video.m3u8" />);

      expect(screen.getByText("Playback Error")).toBeInTheDocument();
    });
  });
});
