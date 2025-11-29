/**
 * Type-safe environment variable access
 *
 * Client-accessible variables must be prefixed with NEXT_PUBLIC_
 * Server-only variables are only accessible in API routes and server components
 */

/**
 * Client-side environment variables (accessible in browser)
 */
export const clientEnv = {
  livekitUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL ?? "",
} as const;

/**
 * Server-side environment variables (only accessible on server)
 * These should never be exposed to the client
 */
export function getServerEnv() {
  if (typeof window !== "undefined") {
    throw new Error("Server environment variables cannot be accessed on the client");
  }

  return {
    livekitApiKey: process.env.LIVEKIT_API_KEY ?? "",
    livekitApiSecret: process.env.LIVEKIT_API_SECRET ?? "",
  } as const;
}

/**
 * Validate that required environment variables are set
 * Call this in API routes or server components to ensure configuration is complete
 */
export function validateServerEnv(): void {
  const env = getServerEnv();

  const missing: string[] = [];

  if (!env.livekitApiKey) {
    missing.push("LIVEKIT_API_KEY");
  }
  if (!env.livekitApiSecret) {
    missing.push("LIVEKIT_API_SECRET");
  }

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
  }
}

/**
 * Validate client environment variables
 * Call this to ensure client configuration is complete
 */
export function validateClientEnv(): void {
  const missing: string[] = [];

  if (!clientEnv.livekitUrl) {
    missing.push("NEXT_PUBLIC_LIVEKIT_URL");
  }

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
  }
}
