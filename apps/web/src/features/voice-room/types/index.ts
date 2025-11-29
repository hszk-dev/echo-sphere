export interface TokenRequest {
  roomName: string;
  participantName: string;
}

export interface TokenResponse {
  token: string;
}

export interface TokenErrorResponse {
  error: string;
}

export interface VoiceRoomProps {
  roomName: string;
  participantName: string;
  onDisconnect?: () => void;
}

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";
