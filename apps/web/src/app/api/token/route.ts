import { AccessToken } from "livekit-server-sdk";
import { type NextRequest, NextResponse } from "next/server";

interface TokenRequest {
  roomName: string;
  participantName: string;
}

interface TokenResponse {
  token: string;
}

interface ErrorResponse {
  error: string;
}

const TOKEN_TTL_SECONDS = 10 * 60; // 10 minutes

export async function POST(
  request: NextRequest
): Promise<NextResponse<TokenResponse | ErrorResponse>> {
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
