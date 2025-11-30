// Re-export shared token types
export type { TokenRequest, TokenResponse, TokenErrorResponse } from "@/shared/types";

export interface VoiceRoomProps {
  roomName: string;
  participantName: string;
  onDisconnect?: () => void;
}

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";
