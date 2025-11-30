"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchRecordings } from "../api/recordings";
import type { RecordingListResponse, RecordingStatus, RecordingSummary } from "../types";

interface RecordingListProps {
  initialPage?: number;
  pageSize?: number;
}

// Status badge component with enhanced styling
function StatusBadge({ status }: { status: RecordingStatus }) {
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
      label: "Recording",
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
      label: "Ready",
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
    <span className={`status-badge ${config.bgClass} ${config.textClass} border border-current/20`}>
      <span
        className={`status-badge-dot ${config.dotClass} ${config.animate ? "animate-pulse" : ""}`}
      />
      {config.label}
    </span>
  );
}

// Format duration in human-readable format
function formatDuration(seconds: number | null): string {
  if (seconds === null) {
    return "--:--";
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// Format date in relative format
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) {
    return "Just now";
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }

  return date.toLocaleDateString();
}

// Recording card component with elevated styling
function RecordingCard({
  recording,
  index = 0,
}: {
  recording: RecordingSummary;
  index?: number;
}) {
  const isPlayable = recording.status === "completed" && recording.playbackUrl;

  // Calculate stagger class (1-9)
  const staggerClass = `stagger-${Math.min(index + 1, 9)}`;

  return (
    <div
      className={`card-elevated p-4 opacity-0 animate-stagger-fade-in ${staggerClass}`}
      style={{ animationFillMode: "forwards" }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 flex-1 mr-3">
          <h3 className="font-medium text-foreground truncate">
            Session {recording.sessionId.slice(-8)}
          </h3>
          <p className="text-sm text-muted">{formatDate(recording.createdAt)}</p>
        </div>
        <StatusBadge status={recording.status} />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-muted">
          <span className="flex items-center gap-1.5">
            <svg
              className="w-4 h-4 opacity-60"
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
            <span className="font-mono text-xs">{formatDuration(recording.durationSeconds)}</span>
          </span>
        </div>

        {isPlayable ? (
          <Link
            href={`/recordings/${recording.id}`}
            className="group flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium
                       hover:bg-primary/90 hover:shadow-glow transition-all duration-300 ease-out-expo"
          >
            <svg
              className="w-4 h-4 transition-transform duration-300 group-hover:scale-110"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
            Play
          </Link>
        ) : (
          <span className="text-sm text-muted/70 italic">
            {recording.status === "processing" ? "Processing..." : "Unavailable"}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Recording list component with pagination
 */
export function RecordingList({ initialPage = 1, pageSize = 20 }: RecordingListProps) {
  const [data, setData] = useState<RecordingListResponse | null>(null);
  const [page, setPage] = useState(initialPage);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadRecordings = useCallback(
    async (currentPage: number) => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchRecordings(currentPage, pageSize);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to load recordings"));
      } finally {
        setIsLoading(false);
      }
    },
    [pageSize]
  );

  useEffect(() => {
    loadRecordings(page);
  }, [page, loadRecordings]);

  // Calculate pagination
  const totalPages = data ? Math.ceil(data.total / data.pageSize) : 0;
  const hasNextPage = page < totalPages;
  const hasPrevPage = page > 1;

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-muted">Loading recordings...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <div className="text-red-500" aria-hidden="true">
          {/* biome-ignore lint/a11y/noSvgWithoutTitle: Decorative icon with aria-hidden parent */}
          <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-foreground font-medium">{error.message}</p>
        <button
          type="button"
          onClick={() => loadRecordings(page)}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!data || data.recordings.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon" aria-hidden="true">
          {/* biome-ignore lint/a11y/noSvgWithoutTitle: Decorative icon with aria-hidden parent */}
          <svg
            className="w-8 h-8 text-primary/70"
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
        <h3 className="empty-state-title">No recordings yet</h3>
        <p className="empty-state-description">
          Start a voice session to create your first recording. Your conversations will be saved
          here for playback.
        </p>
        <Link
          href="/"
          className="group px-5 py-2.5 bg-primary text-white rounded-lg font-medium
                     hover:bg-primary/90 hover:shadow-glow transition-all duration-300 ease-out-expo
                     flex items-center gap-2"
        >
          <svg
            className="w-4 h-4 transition-transform duration-300 group-hover:rotate-90"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Start Session
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <h2 className="text-xl font-display font-bold text-foreground tracking-tight">
            Recordings
          </h2>
          <span className="text-sm font-mono text-muted/70 bg-surface/50 px-2 py-0.5 rounded-md border border-border/50">
            {data.total}
          </span>
        </div>
        <button
          type="button"
          onClick={() => loadRecordings(page)}
          className="group text-sm text-muted hover:text-foreground transition-all duration-300 flex items-center gap-1.5
                     px-3 py-1.5 rounded-lg hover:bg-surface/50 border border-transparent hover:border-border/50"
          disabled={isLoading}
        >
          <svg
            className={`w-4 h-4 transition-transform duration-500 ${isLoading ? "animate-spin" : "group-hover:rotate-180"}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Recording Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.recordings.map((recording, index) => (
          <RecordingCard key={recording.id} recording={recording} index={index} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => setPage((p) => p - 1)}
            disabled={!hasPrevPage || isLoading}
            className="px-4 py-2 bg-surface text-foreground rounded-lg border border-border hover:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-muted">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasNextPage || isLoading}
            className="px-4 py-2 bg-surface text-foreground rounded-lg border border-border hover:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
