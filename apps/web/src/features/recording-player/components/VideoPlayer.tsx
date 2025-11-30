"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useHlsPlayer } from "../hooks/useHlsPlayer";

interface VideoPlayerProps {
  src: string | null;
  onTimeUpdate?: (currentTimeMs: number) => void;
  onDurationChange?: (durationMs: number) => void;
  onError?: (error: Error) => void;
  className?: string;
}

/**
 * HLS Video Player component with playback controls
 */
// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: Complex UI with controls and state
export function VideoPlayer({
  src,
  onTimeUpdate,
  onDurationChange,
  onError,
  className = "",
}: VideoPlayerProps) {
  const { videoRef, state, controls } = useHlsPlayer(src);
  const [showControls, setShowControls] = useState(true);
  const [isHovering, setIsHovering] = useState(false);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-hide controls after 3 seconds of inactivity when playing
  useEffect(() => {
    if (!state.isPlaying || isHovering) {
      setShowControls(true);
      return;
    }

    const timer = setTimeout(() => {
      setShowControls(false);
    }, 3000);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- state.currentTime triggers control visibility reset
  }, [state.isPlaying, isHovering]);

  // Notify parent of time updates (convert to milliseconds)
  useEffect(() => {
    if (onTimeUpdate) {
      onTimeUpdate(state.currentTime * 1000);
    }
  }, [state.currentTime, onTimeUpdate]);

  // Notify parent of duration changes
  useEffect(() => {
    if (onDurationChange && state.duration > 0) {
      onDurationChange(state.duration * 1000);
    }
  }, [state.duration, onDurationChange]);

  // Notify parent of errors
  useEffect(() => {
    if (state.error && onError) {
      onError(state.error);
    }
  }, [state.error, onError]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Toggle play/pause
  const togglePlayback = useCallback(() => {
    if (state.isPlaying) {
      controls.pause();
    } else {
      controls.play();
    }
  }, [state.isPlaying, controls]);

  // Handle progress bar interaction
  const handleProgressInteraction = useCallback(
    (clientX: number, rect: DOMRect) => {
      const percent = (clientX - rect.left) / rect.width;
      controls.seek(percent * state.duration);
    },
    [controls, state.duration]
  );

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    handleProgressInteraction(e.clientX, e.currentTarget.getBoundingClientRect());
  };

  const handleProgressKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const step = state.duration * 0.05; // 5% step
    if (e.key === "ArrowLeft") {
      controls.seek(Math.max(0, state.currentTime - step));
    } else if (e.key === "ArrowRight") {
      controls.seek(Math.min(state.duration, state.currentTime + step));
    }
  };

  // Seek to specific time (in milliseconds) - exposed for transcript sync
  const seekToMs = useCallback(
    (ms: number) => {
      controls.seek(ms / 1000);
    },
    [controls]
  );

  // Store seekToMs in a ref so parent can access it
  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      (video as HTMLVideoElement & { seekToMs?: (ms: number) => void }).seekToMs = seekToMs;
    }
  }, [seekToMs, videoRef]);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if not typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case " ":
        case "k":
          e.preventDefault();
          setActiveKey("space");
          togglePlayback();
          break;
        case "ArrowLeft":
        case "j":
          e.preventDefault();
          setActiveKey("left");
          controls.seek(Math.max(0, state.currentTime - 5));
          break;
        case "ArrowRight":
        case "l":
          e.preventDefault();
          setActiveKey("right");
          controls.seek(Math.min(state.duration, state.currentTime + 5));
          break;
        case "m": {
          e.preventDefault();
          setActiveKey("m");
          const video = videoRef.current;
          if (video) {
            video.muted = !video.muted;
          }
          break;
        }
      }
    };

    const handleKeyUp = () => {
      setActiveKey(null);
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [togglePlayback, controls, state.currentTime, state.duration, videoRef]);

  if (!src) {
    return (
      <div className={`flex items-center justify-center bg-surface rounded-lg ${className}`}>
        <p className="text-muted">No video source available</p>
      </div>
    );
  }

  const progressPercent = state.duration > 0 ? (state.currentTime / state.duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className={`relative bg-black rounded-xl overflow-hidden group/player ${className}`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onMouseMove={() => setShowControls(true)}
    >
      {/* Video Element */}
      {/* biome-ignore lint/a11y/useMediaCaption: Captions are provided via SyncedTranscript component */}
      <video ref={videoRef} className="w-full aspect-video" playsInline />

      {/* Click to play/pause overlay */}
      <button
        type="button"
        className="absolute inset-0 w-full h-full cursor-pointer z-10"
        onClick={togglePlayback}
        aria-label={state.isPlaying ? "Pause" : "Play"}
      />

      {/* Center play button (shown when paused) */}
      {!state.isPlaying && !state.isLoading && !state.error && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
          <div
            className="w-20 h-20 bg-primary/90 rounded-full flex items-center justify-center
                          shadow-glow-lg animate-scale-in backdrop-blur-sm"
          >
            <svg
              className="w-10 h-10 text-white ml-1"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {state.isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-30">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 border-3 border-primary/30 rounded-full" />
              <div className="absolute inset-0 w-12 h-12 border-3 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
            <span className="text-sm text-white/80 font-medium">Loading...</span>
          </div>
        </div>
      )}

      {/* Error Overlay */}
      {state.error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm z-30">
          <div className="text-center p-6 max-w-sm">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <p className="text-red-400 font-medium mb-2">Playback Error</p>
            <p className="text-sm text-white/60">{state.error.message}</p>
          </div>
        </div>
      )}

      {/* Controls */}
      <div
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent
                    pt-16 pb-4 px-4 z-20 transition-all duration-300 ease-out-expo
                    ${showControls ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}
      >
        {/* Progress Bar */}
        <div
          role="slider"
          tabIndex={0}
          aria-label="Video progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(progressPercent)}
          className="h-1.5 bg-white/20 rounded-full cursor-pointer mb-4 group/progress hover:h-2 transition-all duration-200"
          onClick={handleProgressClick}
          onKeyDown={handleProgressKeyDown}
        >
          <div
            className="h-full progress-glow rounded-full relative transition-all duration-100"
            style={{ width: `${progressPercent}%` }}
          >
            <div
              className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full
                            shadow-lg scale-0 group-hover/progress:scale-100 transition-transform duration-200"
            />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between text-white">
          <div className="flex items-center gap-4">
            {/* Play/Pause Button */}
            <button
              type="button"
              onClick={togglePlayback}
              className="group/btn p-2.5 hover:bg-white/10 rounded-full transition-all duration-200
                         hover:scale-110 active:scale-95"
              aria-label={state.isPlaying ? "Pause" : "Play"}
            >
              <div className="relative w-6 h-6">
                {/* Play icon */}
                <svg
                  className={`absolute inset-0 w-6 h-6 transition-all duration-300 ease-out-expo
                              ${state.isPlaying ? "opacity-0 scale-50 rotate-90" : "opacity-100 scale-100 rotate-0"}`}
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
                {/* Pause icon */}
                <svg
                  className={`absolute inset-0 w-6 h-6 transition-all duration-300 ease-out-expo
                              ${state.isPlaying ? "opacity-100 scale-100 rotate-0" : "opacity-0 scale-50 -rotate-90"}`}
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                </svg>
              </div>
            </button>

            {/* Time Display */}
            <div className="flex items-center gap-1.5 text-sm">
              <span className="font-mono text-white/90">{formatTime(state.currentTime)}</span>
              <span className="text-white/40">/</span>
              <span className="font-mono text-white/60">{formatTime(state.duration || 0)}</span>
            </div>
          </div>

          {/* Right side controls */}
          <div className="flex items-center gap-3">
            {/* Keyboard Hints - show on hover */}
            <div
              className={`keyboard-hints transition-opacity duration-200 ${isHovering ? "opacity-100" : "opacity-0"}`}
            >
              <div className="keyboard-hint">
                <span className={`kbd ${activeKey === "space" ? "kbd-active" : ""}`}>Space</span>
                <span>Play</span>
              </div>
              <div className="keyboard-hint">
                <span className={`kbd ${activeKey === "left" ? "kbd-active" : ""}`}>←</span>
                <span className={`kbd ${activeKey === "right" ? "kbd-active" : ""}`}>→</span>
                <span>5s</span>
              </div>
              <div className="keyboard-hint">
                <span className={`kbd ${activeKey === "m" ? "kbd-active" : ""}`}>M</span>
                <span>Mute</span>
              </div>
            </div>

            {/* Volume Control */}
            <button
              type="button"
              onClick={() => {
                const video = videoRef.current;
                if (video) {
                  video.muted = !video.muted;
                }
              }}
              className="p-2.5 hover:bg-white/10 rounded-full transition-all duration-200
                         hover:scale-110 active:scale-95"
              aria-label="Toggle mute"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Export the seek function type for parent components
export type VideoPlayerSeekFn = (ms: number) => void;
