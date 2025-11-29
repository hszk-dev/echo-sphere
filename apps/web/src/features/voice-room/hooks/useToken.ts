"use client";

import { useCallback, useState } from "react";
import type { TokenErrorResponse, TokenRequest, TokenResponse } from "../types";

interface UseTokenState {
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

interface UseTokenReturn extends UseTokenState {
  fetchToken: (request: TokenRequest) => Promise<string | null>;
  clearToken: () => void;
}

export function useToken(): UseTokenReturn {
  const [state, setState] = useState<UseTokenState>({
    token: null,
    isLoading: false,
    error: null,
  });

  const fetchToken = useCallback(async (request: TokenRequest): Promise<string | null> => {
    setState({ token: null, isLoading: true, error: null });

    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData: TokenErrorResponse = await response.json();
        setState({ token: null, isLoading: false, error: errorData.error });
        return null;
      }

      const data: TokenResponse = await response.json();
      setState({ token: data.token, isLoading: false, error: null });
      return data.token;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch token";
      setState({ token: null, isLoading: false, error: errorMessage });
      return null;
    }
  }, []);

  const clearToken = useCallback(() => {
    setState({ token: null, isLoading: false, error: null });
  }, []);

  return {
    ...state,
    fetchToken,
    clearToken,
  };
}
