"use client";

import { forwardRef, useEffect, useRef, useState } from "react";
import type { TranscriptMessage } from "../types";

interface SyncedTranscriptProps {
  transcript: TranscriptMessage[];
  currentTimeMs: number;
  onSeek?: (timestampMs: number) => void;
  className?: string;
}

// Format timestamp for display
function formatTimestamp(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// Get CSS classes for message state with enhanced styling
function getMessageClasses(
  isActive: boolean,
  isPast: boolean,
  isUser: boolean,
  canSeek: boolean,
  wasClicked: boolean
): string {
  const baseClasses = `
    w-full text-left p-3 rounded-xl transition-all duration-300 ease-out-expo
    border border-transparent relative overflow-hidden
  `;
  const alignmentClass = isUser ? "ml-auto max-w-[85%]" : "mr-auto max-w-[85%]";

  let stateClass: string;
  if (isActive) {
    stateClass = `
      bg-primary/15 border-primary/30 ring-2 ring-primary/20
      shadow-[0_0_20px_rgba(255,107,74,0.15)]
    `;
  } else if (isPast) {
    stateClass = "bg-surface/30 opacity-60 hover:opacity-80";
  } else {
    stateClass = "bg-surface/50 hover:bg-surface/70 hover:border-border/50";
  }

  const cursorClass = canSeek ? "cursor-pointer active:scale-[0.98]" : "cursor-default";

  const clickClass = wasClicked ? "highlight-active" : "";

  return `${baseClasses} ${alignmentClass} ${stateClass} ${cursorClass} ${clickClass}`;
}

// Individual message component
interface TranscriptMessageItemProps {
  message: TranscriptMessage;
  isActive: boolean;
  isPast: boolean;
  onSeek?: (timestampMs: number) => void;
}

const TranscriptMessageItem = forwardRef<HTMLButtonElement, TranscriptMessageItemProps>(
  function TranscriptMessageItem({ message, isActive, isPast, onSeek }, ref) {
    const isUser = message.role === "user";
    const [wasClicked, setWasClicked] = useState(false);

    const handleClick = () => {
      if (onSeek) {
        setWasClicked(true);
        onSeek(message.timestampMs);
        // Reset click state after animation
        setTimeout(() => setWasClicked(false), 500);
      }
    };

    return (
      <button
        ref={ref}
        type="button"
        onClick={handleClick}
        className={getMessageClasses(isActive, isPast, isUser, !!onSeek, wasClicked)}
        disabled={!onSeek}
      >
        {/* Active indicator line */}
        {isActive && (
          <div
            className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-primary to-primary/50 rounded-l-xl"
            aria-hidden="true"
          />
        )}

        {/* Header: Role + Timestamp */}
        <div className="flex items-center justify-between mb-1.5">
          <span
            className={`text-xs font-semibold tracking-wide uppercase ${
              isUser ? "text-secondary" : "text-primary"
            }`}
          >
            {isUser ? "You" : "AI Assistant"}
          </span>
          <span
            className={`text-xs font-mono px-1.5 py-0.5 rounded ${
              isActive ? "bg-primary/20 text-primary" : "text-muted/70"
            }`}
          >
            {formatTimestamp(message.timestampMs)}
          </span>
        </div>

        {/* Content */}
        <p
          className={`text-sm leading-relaxed ${
            isActive ? "text-foreground font-medium" : "text-foreground/75"
          }`}
        >
          {message.content}
        </p>
      </button>
    );
  }
);

/**
 * Transcript component with automatic scrolling and click-to-seek functionality
 */
export function SyncedTranscript({
  transcript,
  currentTimeMs,
  onSeek,
  className = "",
}: SyncedTranscriptProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeMessageRef = useRef<HTMLButtonElement>(null);

  // Find the currently active message based on playback time
  const activeMessageIndex = transcript.reduce((activeIdx, msg, idx) => {
    if (msg.timestampMs <= currentTimeMs) {
      return idx;
    }
    return activeIdx;
  }, -1);

  // Auto-scroll to active message
  useEffect(() => {
    const activeElement = activeMessageRef.current;
    const container = containerRef.current;
    if (!activeElement || !container) {
      return;
    }

    const containerRect = container.getBoundingClientRect();
    const elementRect = activeElement.getBoundingClientRect();

    // Only scroll if element is not fully visible
    const isOutOfView =
      elementRect.top < containerRect.top || elementRect.bottom > containerRect.bottom;

    if (isOutOfView) {
      activeElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  });

  if (transcript.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
        <div className="w-12 h-12 mb-4 rounded-full bg-surface/50 flex items-center justify-center">
          <svg
            className="w-6 h-6 text-muted/50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <p className="text-muted text-sm">No transcript available</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={`overflow-y-auto scroll-smooth no-scrollbar ${className}`}>
      <div className="space-y-2 p-4">
        {transcript.map((message, idx) => (
          <TranscriptMessageItem
            key={message.id}
            ref={idx === activeMessageIndex ? activeMessageRef : null}
            message={message}
            isActive={idx === activeMessageIndex}
            isPast={idx < activeMessageIndex}
            onSeek={onSeek}
          />
        ))}
      </div>
    </div>
  );
}
