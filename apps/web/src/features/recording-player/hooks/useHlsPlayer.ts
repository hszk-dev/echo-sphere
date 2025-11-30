"use client";

import Hls from "hls.js";
import { useCallback, useEffect, useRef, useState } from "react";

interface HlsPlayerState {
  isLoading: boolean;
  isReady: boolean;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  error: Error | null;
}

interface HlsPlayerControls {
  play: () => Promise<void>;
  pause: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
}

interface UseHlsPlayerResult {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  state: HlsPlayerState;
  controls: HlsPlayerControls;
}

/**
 * Custom hook for HLS.js video player integration
 * Handles HLS stream loading, playback controls, and state management
 */
export function useHlsPlayer(src: string | null): UseHlsPlayerResult {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);

  const [state, setState] = useState<HlsPlayerState>({
    isLoading: false,
    isReady: false,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    error: null,
  });

  // Initialize HLS instance when src changes
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) {
      return;
    }

    // Clean up previous instance
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    // Check if HLS is supported
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
      });

      hlsRef.current = hls;

      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setState((prev) => ({ ...prev, isLoading: false, isReady: true }));
      });

      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) {
          const error = new Error(`HLS Error: ${data.type} - ${data.details}`);
          setState((prev) => ({ ...prev, isLoading: false, error }));

          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              // Try to recover network error
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              // Try to recover media error
              hls.recoverMediaError();
              break;
            default:
              // Cannot recover
              hls.destroy();
              break;
          }
        }
      });

      return () => {
        hls.destroy();
        hlsRef.current = null;
      };
    }
    // For Safari which has native HLS support
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      setState((prev) => ({ ...prev, isLoading: false, isReady: true }));

      return () => {
        video.src = "";
      };
    }
    // HLS not supported
    const error = new Error("HLS is not supported in this browser");
    setState((prev) => ({ ...prev, isLoading: false, error }));
    return;
  }, [src]);

  // Set up video event listeners
  useEffect(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    const handleTimeUpdate = () => {
      setState((prev) => ({ ...prev, currentTime: video.currentTime }));
    };

    const handleDurationChange = () => {
      setState((prev) => ({ ...prev, duration: video.duration }));
    };

    const handlePlay = () => {
      setState((prev) => ({ ...prev, isPlaying: true }));
    };

    const handlePause = () => {
      setState((prev) => ({ ...prev, isPlaying: false }));
    };

    const handleEnded = () => {
      setState((prev) => ({ ...prev, isPlaying: false }));
    };

    const handleError = () => {
      const error = new Error(video.error?.message || "Video playback error");
      setState((prev) => ({ ...prev, error }));
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("durationchange", handleDurationChange);
    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("ended", handleEnded);
    video.addEventListener("error", handleError);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("durationchange", handleDurationChange);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("ended", handleEnded);
      video.removeEventListener("error", handleError);
    };
  }, []);

  // Playback controls
  const play = useCallback(async () => {
    const video = videoRef.current;
    if (video) {
      try {
        await video.play();
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: err instanceof Error ? err : new Error("Playback failed"),
        }));
      }
    }
  }, []);

  const pause = useCallback(() => {
    const video = videoRef.current;
    if (video) {
      video.pause();
    }
  }, []);

  const seek = useCallback((time: number) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
    }
  }, []);

  const setVolume = useCallback((volume: number) => {
    const video = videoRef.current;
    if (video) {
      video.volume = Math.max(0, Math.min(1, volume));
    }
  }, []);

  return {
    videoRef,
    state,
    controls: { play, pause, seek, setVolume },
  };
}
