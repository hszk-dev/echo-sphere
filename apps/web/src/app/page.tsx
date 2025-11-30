"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

export default function HomePage() {
  const router = useRouter();
  const [roomName, setRoomName] = useState("");

  const handleCreateRoom = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const name = roomName.trim() || `room-${Math.random().toString(36).substring(2, 9)}`;
      router.push(`/room/${encodeURIComponent(name)}`);
    },
    [roomName, router]
  );

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-12 text-center">
          <h1 className="font-display text-4xl font-bold sm:text-5xl">
            <span className="gradient-text">EchoSphere</span>
          </h1>
          <p className="mt-4 text-muted">Real-time AI voice interaction platform</p>
        </div>

        <div className="glass rounded-2xl p-6 sm:p-8">
          <h2 className="mb-6 text-center font-display text-xl font-semibold sm:text-2xl">
            Create or Join a Room
          </h2>

          <form onSubmit={handleCreateRoom} className="space-y-6">
            <div>
              <label htmlFor="roomName" className="mb-2 block text-sm font-medium">
                Room Name
              </label>
              <input
                id="roomName"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="Enter room name (optional)"
                className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-foreground placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="mt-2 text-xs text-muted">
                Leave empty to create a room with a random name.
              </p>
            </div>

            <button
              type="submit"
              className="glow-hover w-full rounded-lg bg-primary px-4 py-3 font-medium text-primary-foreground transition-all hover:opacity-90"
            >
              Enter Room
            </button>
          </form>
        </div>

        <p className="mt-8 text-center text-xs text-muted">
          Start a voice conversation with AI. No account required.
        </p>
      </div>
    </main>
  );
}
