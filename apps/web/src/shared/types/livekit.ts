/**
 * LiveKit token request/response types
 * Used by both API routes and client-side hooks
 */

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
