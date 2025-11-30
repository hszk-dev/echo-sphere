"use client";

import { useSessionMessages } from "@livekit/components-react";
import { useEffect, useRef } from "react";

export function TranscriptPanel() {
  const { messages } = useSessionMessages();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive.
  // This is a common React pattern for chat interfaces where the dependency
  // serves as a trigger rather than a value used in the effect body.
  // See: https://react.dev/reference/react/useEffect#specifying-reactive-dependencies
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
      {messages.map((msg) => {
        const isUser = msg.type === "userTranscript";
        return (
          <div
            key={msg.id}
            className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}
          >
            <span className="text-xs text-muted">{isUser ? "You" : "Agent"}</span>
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                isUser ? "bg-primary text-primary-foreground" : "bg-surface text-foreground"
              }`}
            >
              {msg.message}
            </div>
          </div>
        );
      })}
    </div>
  );
}
