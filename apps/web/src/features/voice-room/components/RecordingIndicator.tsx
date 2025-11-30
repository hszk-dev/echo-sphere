"use client";

import { useState } from "react";

export type RecordingState = "idle" | "starting" | "recording" | "stopping" | "stopped" | "error";

interface RecordingIndicatorProps {
  state: RecordingState;
  durationSeconds?: number;
  onToggle?: () => void;
  disabled?: boolean;
}

// Format duration as MM:SS
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Recording indicator component for the voice room
 * Shows recording status with visual feedback and optional toggle control
 */
// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: UI component with multiple states
export function RecordingIndicator({
  state,
  durationSeconds = 0,
  onToggle,
  disabled = false,
}: RecordingIndicatorProps) {
  const [isHovered, setIsHovered] = useState(false);

  const isRecording = state === "recording";
  const isTransitioning = state === "starting" || state === "stopping";
  const hasError = state === "error";
  const canToggle = !disabled && !isTransitioning && onToggle;

  // Status text based on state
  const statusText: Record<RecordingState, string> = {
    idle: "Not Recording",
    starting: "Starting...",
    recording: `Recording ${formatDuration(durationSeconds)}`,
    stopping: "Stopping...",
    stopped: "Recording Stopped",
    error: "Recording Error",
  };

  // Button text based on state and hover
  const getButtonText = () => {
    if (isTransitioning) {
      return statusText[state];
    }
    if (isRecording && isHovered) {
      return "Stop Recording";
    }
    if (!isRecording && isHovered) {
      return "Start Recording";
    }
    return statusText[state];
  };

  return (
    <div className="flex items-center gap-3">
      {/* Recording Indicator Dot */}
      <div className="relative flex items-center justify-center w-4 h-4">
        {isRecording && (
          <>
            {/* Pulsing ring */}
            <div className="absolute w-4 h-4 bg-red-500/30 rounded-full animate-ping" />
            {/* Solid dot */}
            <div className="relative w-3 h-3 bg-red-500 rounded-full" />
          </>
        )}
        {isTransitioning && (
          <div className="w-3 h-3 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
        )}
        {hasError && <div className="w-3 h-3 bg-red-500 rounded-full" />}
        {(state === "idle" || state === "stopped") && (
          <div className="w-3 h-3 bg-muted rounded-full" />
        )}
      </div>

      {/* Toggle Button */}
      {onToggle ? (
        <button
          type="button"
          onClick={onToggle}
          disabled={!canToggle}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className={`
            px-3 py-1.5 rounded-lg text-sm font-medium transition-all
            ${
              isRecording
                ? "bg-red-500/10 text-red-500 hover:bg-red-500/20"
                : hasError
                  ? "bg-red-500/10 text-red-500"
                  : "bg-surface hover:bg-surface/80 text-foreground"
            }
            ${isTransitioning ? "opacity-70 cursor-wait" : ""}
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
            ${canToggle ? "cursor-pointer" : ""}
          `}
        >
          {getButtonText()}
        </button>
      ) : (
        <span
          className={`
            text-sm font-medium
            ${isRecording ? "text-red-500" : hasError ? "text-red-500" : "text-muted"}
          `}
        >
          {statusText[state]}
        </span>
      )}
    </div>
  );
}

/**
 * Hook to manage recording state (for future integration with backend)
 * Currently returns mock data
 */
export function useRecordingState() {
  const [state, setState] = useState<RecordingState>("idle");
  // Duration tracking will be implemented with actual recording logic
  const [durationSeconds] = useState(0);

  // Start recording timer when recording
  // This will be replaced with actual recording logic
  const startRecording = () => {
    setState("starting");
    // Simulate starting delay
    setTimeout(() => {
      setState("recording");
    }, 1000);
  };

  const stopRecording = () => {
    setState("stopping");
    // Simulate stopping delay
    setTimeout(() => {
      setState("stopped");
    }, 1000);
  };

  const toggleRecording = () => {
    if (state === "recording") {
      stopRecording();
    } else if (state === "idle" || state === "stopped") {
      startRecording();
    }
  };

  return {
    state,
    durationSeconds,
    toggleRecording,
    startRecording,
    stopRecording,
  };
}
