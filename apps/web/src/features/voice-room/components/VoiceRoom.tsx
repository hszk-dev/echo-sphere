"use client";

import "@livekit/components-styles";
import { clientEnv } from "@/config/env";
import {
  BarVisualizer,
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useConnectionState,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useCallback, useEffect, useState } from "react";
import { useToken } from "../hooks/useToken";
import type { VoiceRoomProps } from "../types";

function ConnectionStatus() {
  const connectionState = useConnectionState();

  const statusText: Record<ConnectionState, string> = {
    [ConnectionState.Disconnected]: "Disconnected",
    [ConnectionState.Connecting]: "Connecting...",
    [ConnectionState.Connected]: "Connected",
    [ConnectionState.Reconnecting]: "Reconnecting...",
    [ConnectionState.SignalReconnecting]: "Reconnecting...",
  };

  const statusColor: Record<ConnectionState, string> = {
    [ConnectionState.Disconnected]: "text-red-500",
    [ConnectionState.Connecting]: "text-yellow-500",
    [ConnectionState.Connected]: "text-green-500",
    [ConnectionState.Reconnecting]: "text-yellow-500",
    [ConnectionState.SignalReconnecting]: "text-yellow-500",
  };

  return (
    <div className={`text-sm font-medium ${statusColor[connectionState]}`}>
      {statusText[connectionState]}
    </div>
  );
}

function AgentVisualizer() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="text-sm text-gray-500 dark:text-gray-400">Agent: {state}</div>
      <div className="h-32 w-full max-w-md">
        <BarVisualizer
          state={state}
          trackRef={audioTrack}
          barCount={5}
          options={{ minHeight: 8 }}
        />
      </div>
    </div>
  );
}

function RoomContent() {
  return (
    <div className="flex flex-col items-center gap-8 p-8">
      <ConnectionStatus />
      <AgentVisualizer />
      <RoomAudioRenderer />
      <VoiceAssistantControlBar />
    </div>
  );
}

export function VoiceRoom({ roomName, participantName, onDisconnect }: VoiceRoomProps) {
  const { token, isLoading, error, fetchToken, clearToken } = useToken();
  const [shouldConnect, setShouldConnect] = useState(false);

  useEffect(() => {
    fetchToken({ roomName, participantName });
  }, [roomName, participantName, fetchToken]);

  useEffect(() => {
    if (token) {
      setShouldConnect(true);
    }
  }, [token]);

  const handleDisconnect = useCallback(() => {
    setShouldConnect(false);
    clearToken();
    onDisconnect?.();
  }, [clearToken, onDisconnect]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500 dark:text-gray-400">Connecting to room...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!token) {
    return null;
  }

  return (
    <LiveKitRoom
      serverUrl={clientEnv.livekitUrl}
      token={token}
      connect={shouldConnect}
      audio={true}
      video={false}
      onDisconnected={handleDisconnect}
    >
      <RoomContent />
    </LiveKitRoom>
  );
}
