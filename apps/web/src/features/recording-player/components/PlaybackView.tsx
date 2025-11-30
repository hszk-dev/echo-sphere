"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchRecordingDetail } from "../api/recordings";
import type { RecordingDetail, RecordingStatus } from "../types";
import { SyncedTranscript } from "./SyncedTranscript";
import { VideoPlayer } from "./VideoPlayer";

interface PlaybackViewProps {
  recordingId: string;
}

// Status badge for recording detail with enhanced styling
function DetailStatusBadge({ status }: { status: RecordingStatus }) {
  const statusConfig: Record<
    RecordingStatus,
    { label: string; bgClass: string; textClass: string; dotClass: string; animate?: boolean }
  > = {
    starting: {
      label: "Starting",
      bgClass: "bg-yellow-500/10",
      textClass: "text-yellow-400",
      dotClass: "bg-yellow-400",
      animate: true,
    },
    active: {
      label: "Recording in Progress",
      bgClass: "bg-red-500/10",
      textClass: "text-red-400",
      dotClass: "bg-red-400",
      animate: true,
    },
    processing: {
      label: "Processing",
      bgClass: "bg-blue-500/10",
      textClass: "text-blue-400",
      dotClass: "bg-blue-400",
      animate: true,
    },
    completed: {
      label: "Ready to Play",
      bgClass: "bg-green-500/10",
      textClass: "text-green-400",
      dotClass: "bg-green-400",
    },
    failed: {
      label: "Failed",
      bgClass: "bg-red-500/10",
      textClass: "text-red-400",
      dotClass: "bg-red-400",
    },
  };

  const config = statusConfig[status];

  return (
    <span
      className={`status-badge px-3 py-1.5 ${config.bgClass} ${config.textClass} border border-current/20`}
    >
      <span
        className={`status-badge-dot ${config.dotClass} ${config.animate ? "animate-pulse" : ""}`}
      />
      {config.label}
    </span>
  );
}

// Format file size
function formatFileSize(bytes: number | null): string {
  if (bytes === null) {
    return "--";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Format duration
function formatDuration(seconds: number | null): string {
  if (seconds === null) {
    return "--:--";
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// Format date
function formatDateTime(dateString: string | null): string {
  if (!dateString) {
    return "--";
  }
  return new Date(dateString).toLocaleString();
}

/**
 * Full playback view with video player, transcript, and recording details
 */
// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: Complex UI with multiple states
export function PlaybackView({ recordingId }: PlaybackViewProps) {
  const [recording, setRecording] = useState<RecordingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);

  // Load recording detail
  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await fetchRecordingDetail(recordingId, controller.signal);
        setRecording(data);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err);
        }
      } finally {
        setIsLoading(false);
      }
    }

    load();

    return () => controller.abort();
  }, [recordingId]);

  // Handle time update from video player
  const handleTimeUpdate = useCallback((timeMs: number) => {
    setCurrentTimeMs(timeMs);
  }, []);

  // Handle seek from transcript
  const handleTranscriptSeek = useCallback((timestampMs: number) => {
    // Access the video element's seekToMs function
    const video = document.querySelector("video") as HTMLVideoElement & {
      seekToMs?: (ms: number) => void;
    };
    if (video?.seekToMs) {
      video.seekToMs(timestampMs);
    } else if (video) {
      video.currentTime = timestampMs / 1000;
    }
  }, []);

  // Handle video error
  const handleVideoError = useCallback((err: Error) => {
    console.error("Video playback error:", err);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-muted">Loading recording...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="text-red-500" aria-hidden="true">
          {/* biome-ignore lint/a11y/noSvgWithoutTitle: Decorative icon with aria-hidden parent */}
          <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-xl font-medium text-foreground">{error.message}</p>
        <Link
          href="/recordings"
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          Back to Recordings
        </Link>
      </div>
    );
  }

  if (!recording) {
    return null;
  }

  const isPlayable = recording.status === "completed" && recording.playbackUrl;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/recordings"
            className="p-2 hover:bg-surface rounded-lg transition-colors"
            aria-label="Back to recordings"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </Link>
          <div>
            <h1 className="text-xl font-semibold text-foreground">
              Session {recording.sessionId.slice(-8)}
            </h1>
            <p className="text-sm text-muted">{formatDateTime(recording.createdAt)}</p>
          </div>
        </div>
        <DetailStatusBadge status={recording.status} />
      </div>

      {/* Main Content */}
      {isPlayable ? (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Video Player - 2 columns */}
          <div className="lg:col-span-2">
            <VideoPlayer
              src={recording.playbackUrl}
              onTimeUpdate={handleTimeUpdate}
              onError={handleVideoError}
              className="w-full"
            />

            {/* Recording Info */}
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="card-elevated p-4 text-center group/stat">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <svg
                    className="w-4 h-4 text-muted group-hover/stat:text-primary transition-colors duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="text-xs text-muted uppercase tracking-wider">Duration</p>
                </div>
                <p className="text-xl font-mono font-medium text-foreground">
                  {formatDuration(recording.durationSeconds)}
                </p>
              </div>
              <div className="card-elevated p-4 text-center group/stat">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <svg
                    className="w-4 h-4 text-muted group-hover/stat:text-primary transition-colors duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                    />
                  </svg>
                  <p className="text-xs text-muted uppercase tracking-wider">File Size</p>
                </div>
                <p className="text-xl font-mono font-medium text-foreground">
                  {formatFileSize(recording.fileSizeBytes)}
                </p>
              </div>
              <div className="card-elevated p-4 text-center group/stat">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <svg
                    className="w-4 h-4 text-muted group-hover/stat:text-primary transition-colors duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                  <p className="text-xs text-muted uppercase tracking-wider">Messages</p>
                </div>
                <p className="text-xl font-mono font-medium text-foreground">
                  {recording.transcript.length}
                </p>
              </div>
            </div>
          </div>

          {/* Transcript Panel - 1 column */}
          <div className="lg:col-span-1">
            <div className="card-elevated h-[500px] flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border/50 bg-surface/30">
                <div className="flex items-center gap-2 mb-1">
                  <svg
                    className="w-4 h-4 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                  <h2 className="font-display font-semibold text-foreground">Transcript</h2>
                </div>
                <p className="text-xs text-muted/70">Click on a message to jump to that moment</p>
              </div>
              <SyncedTranscript
                transcript={recording.transcript}
                currentTimeMs={currentTimeMs}
                onSeek={handleTranscriptSeek}
                className="flex-1"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-surface rounded-lg border border-border p-8 text-center">
          <div className="text-muted mb-4" aria-hidden="true">
            {/* biome-ignore lint/a11y/noSvgWithoutTitle: Decorative icon with aria-hidden parent */}
            <svg
              className="w-16 h-16 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">
            {recording.status === "processing"
              ? "Recording is being processed"
              : recording.status === "active"
                ? "Recording in progress"
                : recording.status === "starting"
                  ? "Recording is starting"
                  : "Recording unavailable"}
          </h3>
          <p className="text-sm text-muted">
            {recording.status === "processing"
              ? "This recording is being processed. Please check back in a few minutes."
              : recording.status === "active"
                ? "This recording is currently in progress. It will be available for playback once completed."
                : recording.status === "failed"
                  ? "This recording failed to process. Please try creating a new recording."
                  : "Please wait while the recording starts."}
          </p>
        </div>
      )}
    </div>
  );
}
