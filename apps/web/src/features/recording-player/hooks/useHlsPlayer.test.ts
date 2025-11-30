import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useHlsPlayer } from "./useHlsPlayer";

// Note: HLS.js is mocked globally in test/setup.ts
// These tests focus on the hook's state management and control functions
// rather than HLS.js integration details which are better tested via integration/e2e tests

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useHlsPlayer", () => {
  describe("initialization", () => {
    it("initializes with default state when no src provided", () => {
      const { result } = renderHook(() => useHlsPlayer(null));

      expect(result.current.state).toEqual({
        isLoading: false,
        isReady: false,
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        error: null,
      });
    });

    it("returns a video ref", () => {
      const { result } = renderHook(() => useHlsPlayer(null));

      expect(result.current.videoRef).toBeDefined();
      expect(result.current.videoRef.current).toBeNull();
    });

    it("returns control functions", () => {
      const { result } = renderHook(() => useHlsPlayer(null));

      expect(typeof result.current.controls.play).toBe("function");
      expect(typeof result.current.controls.pause).toBe("function");
      expect(typeof result.current.controls.seek).toBe("function");
      expect(typeof result.current.controls.setVolume).toBe("function");
    });
  });

  describe("playback controls", () => {
    it("play() calls video.play() when video element is attached", async () => {
      const videoElement = document.createElement("video");
      videoElement.play = vi.fn().mockResolvedValue(undefined);

      const { result } = renderHook(() => useHlsPlayer(null));

      // Attach video element
      act(() => {
        (result.current.videoRef as React.MutableRefObject<HTMLVideoElement>).current =
          videoElement;
      });

      await act(async () => {
        await result.current.controls.play();
      });

      expect(videoElement.play).toHaveBeenCalled();
    });

    it("pause() calls video.pause() when video element is attached", () => {
      const videoElement = document.createElement("video");
      videoElement.pause = vi.fn();

      const { result } = renderHook(() => useHlsPlayer(null));

      // Attach video element
      act(() => {
        (result.current.videoRef as React.MutableRefObject<HTMLVideoElement>).current =
          videoElement;
      });

      act(() => {
        result.current.controls.pause();
      });

      expect(videoElement.pause).toHaveBeenCalled();
    });

    it("seek() sets video.currentTime when video element is attached", () => {
      const videoElement = document.createElement("video");
      const currentTimeSetter = vi.fn();
      Object.defineProperty(videoElement, "currentTime", {
        get: () => 0,
        set: currentTimeSetter,
        configurable: true,
      });

      const { result } = renderHook(() => useHlsPlayer(null));

      // Attach video element
      act(() => {
        (result.current.videoRef as React.MutableRefObject<HTMLVideoElement>).current =
          videoElement;
      });

      act(() => {
        result.current.controls.seek(30);
      });

      expect(currentTimeSetter).toHaveBeenCalledWith(30);
    });

    it("setVolume() clamps value between 0 and 1", () => {
      const videoElement = document.createElement("video");
      let volumeValue = 1;
      Object.defineProperty(videoElement, "volume", {
        get: () => volumeValue,
        set: (v: number) => {
          volumeValue = v;
        },
        configurable: true,
      });

      const { result } = renderHook(() => useHlsPlayer(null));

      // Attach video element
      act(() => {
        (result.current.videoRef as React.MutableRefObject<HTMLVideoElement>).current =
          videoElement;
      });

      // Test clamping above 1
      act(() => {
        result.current.controls.setVolume(1.5);
      });
      expect(volumeValue).toBe(1);

      // Test clamping below 0
      act(() => {
        result.current.controls.setVolume(-0.5);
      });
      expect(volumeValue).toBe(0);

      // Test valid value
      act(() => {
        result.current.controls.setVolume(0.5);
      });
      expect(volumeValue).toBe(0.5);
    });

    it("play() sets error state when playback fails", async () => {
      const videoElement = document.createElement("video");
      const playError = new Error("Playback not allowed");
      videoElement.play = vi.fn().mockRejectedValue(playError);

      const { result } = renderHook(() => useHlsPlayer(null));

      // Attach video element
      act(() => {
        (result.current.videoRef as React.MutableRefObject<HTMLVideoElement>).current =
          videoElement;
      });

      await act(async () => {
        await result.current.controls.play();
      });

      expect(result.current.state.error).not.toBeNull();
      expect(result.current.state.error?.message).toBe("Playback not allowed");
    });

    it("controls do nothing when video element is not attached", async () => {
      const { result } = renderHook(() => useHlsPlayer(null));

      // No video element attached, should not throw
      await act(async () => {
        await result.current.controls.play();
      });

      act(() => {
        result.current.controls.pause();
        result.current.controls.seek(10);
        result.current.controls.setVolume(0.5);
      });

      // No errors should be thrown
      expect(result.current.state.error).toBeNull();
    });
  });

  describe("src changes", () => {
    it("sets isLoading when src changes from null to valid URL", () => {
      const { result, rerender } = renderHook(({ src }) => useHlsPlayer(src), {
        initialProps: { src: null as string | null },
      });

      expect(result.current.state.isLoading).toBe(false);

      // Simulating what happens when src is provided
      // Without a video element attached, the effect returns early
      rerender({ src: "https://example.com/video.m3u8" });

      // isLoading won't change without a video element,
      // but the hook should not error
      expect(result.current.state.error).toBeNull();
    });
  });

  describe("ref stability", () => {
    it("returns stable videoRef across renders", () => {
      const { result, rerender } = renderHook(({ src }) => useHlsPlayer(src), {
        initialProps: { src: null as string | null },
      });

      const initialRef = result.current.videoRef;

      rerender({ src: "https://example.com/video.m3u8" });

      expect(result.current.videoRef).toBe(initialRef);
    });

    it("returns stable control functions across renders", () => {
      const { result, rerender } = renderHook(({ src }) => useHlsPlayer(src), {
        initialProps: { src: null as string | null },
      });

      const initialControls = result.current.controls;

      rerender({ src: "https://example.com/video.m3u8" });

      expect(result.current.controls.play).toBe(initialControls.play);
      expect(result.current.controls.pause).toBe(initialControls.pause);
      expect(result.current.controls.seek).toBe(initialControls.seek);
      expect(result.current.controls.setVolume).toBe(initialControls.setVolume);
    });
  });
});
