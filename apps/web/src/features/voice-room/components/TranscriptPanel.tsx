"use client";

import { useTranscriptions, useVoiceAssistant } from "@livekit/components-react";
import { useEffect, useMemo, useRef } from "react";

interface TranscriptMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: number;
}

export function TranscriptPanel() {
  const { agentTranscriptions } = useVoiceAssistant();
  const userTranscriptions = useTranscriptions();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Combine and sort messages from agent and user transcriptions
  const messages = useMemo<TranscriptMessage[]>(() => {
    const combined: TranscriptMessage[] = [];

    // Add agent transcriptions
    for (const segment of agentTranscriptions) {
      combined.push({
        id: `agent-${segment.id}`,
        text: segment.text,
        isUser: false,
        timestamp: segment.firstReceivedTime,
      });
    }

    // Add user transcriptions
    for (const stream of userTranscriptions) {
      combined.push({
        id: `user-${stream.streamInfo.id}`,
        text: stream.text,
        isUser: true,
        timestamp: Date.now(), // Use current time as fallback since TextStreamData doesn't have timestamp
      });
    }

    // Sort by timestamp
    return combined.sort((a, b) => a.timestamp - b.timestamp);
  }, [agentTranscriptions, userTranscriptions]);

  // Auto-scroll to bottom when new messages arrive.
  // messages.length is used as a trigger to scroll when new messages arrive,
  // not as a value used in the effect body. This is a common React pattern for chat UIs.
  // biome-ignore lint/correctness/useExhaustiveDependencies: messages.length triggers scroll on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted">
        Conversation will appear here...
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex h-full flex-col gap-3 overflow-y-auto p-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex flex-col gap-1 ${msg.isUser ? "items-end" : "items-start"}`}
        >
          <span className="text-xs text-muted">{msg.isUser ? "You" : "Agent"}</span>
          <div
            className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
              msg.isUser ? "bg-primary text-primary-foreground" : "bg-surface text-foreground"
            }`}
          >
            {msg.text}
          </div>
        </div>
      ))}
    </div>
  );
}
