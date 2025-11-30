import type { TokenErrorResponse, TokenRequest, TokenResponse } from "@/shared/types";
import { AccessToken } from "livekit-server-sdk";
import { type NextRequest, NextResponse } from "next/server";

const TOKEN_TTL_SECONDS = 10 * 60; // 10 minutes
const MAX_NAME_LENGTH = 128;

export async function POST(
  request: NextRequest
): Promise<NextResponse<TokenResponse | TokenErrorResponse>> {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;

  if (!apiKey || !apiSecret) {
    return NextResponse.json(
      { error: "Server misconfigured: Missing LiveKit credentials" },
      { status: 500 }
    );
  }

  let body: TokenRequest;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { roomName, participantName } = body;

  if (!roomName || !participantName) {
    return NextResponse.json({ error: "Missing roomName or participantName" }, { status: 400 });
  }

  if (roomName.length > MAX_NAME_LENGTH || participantName.length > MAX_NAME_LENGTH) {
    return NextResponse.json(
      { error: `Name must be ${MAX_NAME_LENGTH} characters or less` },
      { status: 400 }
    );
  }

  const accessToken = new AccessToken(apiKey, apiSecret, {
    identity: participantName,
    ttl: TOKEN_TTL_SECONDS,
  });

  accessToken.addGrant({
    roomJoin: true,
    room: roomName,
    canPublish: true,
    canSubscribe: true,
  });

  const token = await accessToken.toJwt();

  return NextResponse.json({ token });
}
