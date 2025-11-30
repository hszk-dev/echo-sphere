"use client";

import { VoiceRoom } from "@/features/voice-room";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useState } from "react";

type RoomPageState = "input" | "connected";

export default function RoomPage() {
  const params = useParams();
  const router = useRouter();
  const roomId = params.roomId as string;

  const [state, setState] = useState<RoomPageState>("input");
  const [participantName, setParticipantName] = useState("");
  const [inputValue, setInputValue] = useState("");

  const handleJoin = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const name = inputValue.trim() || `Guest-${Math.random().toString(36).substring(2, 7)}`;
      setParticipantName(name);
      setState("connected");
    },
    [inputValue]
  );

  const handleDisconnect = useCallback(() => {
    setState("input");
    setParticipantName("");
    setInputValue("");
  }, []);

  const handleBack = useCallback(() => {
    router.push("/");
  }, [router]);

  if (state === "connected" && participantName) {
    return (
      <main className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-border px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDisconnect}
              className="rounded-lg p-2 text-muted transition-colors hover:bg-surface hover:text-foreground"
              aria-label="Leave room"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="m12 19-7-7 7-7" />
                <path d="M19 12H5" />
              </svg>
            </button>
            <div>
              <h1 className="font-display text-lg font-bold sm:text-xl">{roomId}</h1>
              <p className="text-xs text-muted sm:text-sm">
                Joined as <span className="text-foreground">{participantName}</span>
              </p>
            </div>
          </div>
        </header>

        <div className="flex flex-1 items-center justify-center p-4">
          <VoiceRoom
            roomName={roomId}
            participantName={participantName}
            onDisconnect={handleDisconnect}
          />
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <button
          type="button"
          onClick={handleBack}
          className="mb-8 flex items-center gap-2 text-sm text-muted transition-colors hover:text-foreground"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="m12 19-7-7 7-7" />
            <path d="M19 12H5" />
          </svg>
          Back to home
        </button>

        <div className="glass rounded-2xl p-6 sm:p-8">
          <div className="mb-6 text-center">
            <h1 className="font-display text-2xl font-bold sm:text-3xl">Join Room</h1>
            <p className="mt-2 text-sm text-muted sm:text-base">
              Joining room: <span className="font-mono text-foreground">{roomId}</span>
            </p>
          </div>

          <form onSubmit={handleJoin} className="space-y-6">
            <div>
              <label htmlFor="participantName" className="mb-2 block text-sm font-medium">
                Your Name
              </label>
              <input
                id="participantName"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter your name (optional)"
                className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-foreground placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="mt-2 text-xs text-muted">
                Leave empty to join as a guest with a random name.
              </p>
            </div>

            <button
              type="submit"
              className="glow-hover w-full rounded-lg bg-primary px-4 py-3 font-medium text-primary-foreground transition-all hover:opacity-90"
            >
              Join Room
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
