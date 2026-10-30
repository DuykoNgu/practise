"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useSyncExternalStore } from "react";

import { LOGIN_PATH } from "@/lib/routes";
import {
  clearSessionCookie,
  readSessionToken,
  parseSession,
  type Session,
} from "@/lib/session";

export type SessionState =
  | { status: "loading"; session: null }
  | { status: "authenticated"; session: Session }
  | { status: "unauthenticated"; session: null };

const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notifyAll(): void {
  listeners.forEach((listener) => listener());
}

function getServerSnapshot(): undefined {
  return undefined;
}

export function useSession() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const token = useSyncExternalStore<string | null | undefined>(
    subscribe,
    readSessionToken,
    getServerSnapshot,
  );

  const state = useMemo<SessionState>(() => {
    if (token === undefined) return { status: "loading", session: null };
    const session = parseSession(token ?? undefined);
    return session
      ? { status: "authenticated", session }
      : { status: "unauthenticated", session: null };
  }, [token]);

  useEffect(() => {
    if (state.status === "unauthenticated") router.replace(LOGIN_PATH);
  }, [state.status, router]);

  const signOut = useCallback(() => {
    clearSessionCookie();
    queryClient.clear();
    notifyAll();
  }, [queryClient]);

  const expiresAt = state.session?.expiresAt.getTime();
  useEffect(() => {
    if (expiresAt === undefined) return;
    const timer = setTimeout(signOut, Math.max(expiresAt - Date.now(), 0));
    return () => clearTimeout(timer);
  }, [expiresAt, signOut]);

  return { ...state, signOut };
}
