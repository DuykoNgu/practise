import type { components } from "@/lib/api-types";

export type Role = components["schemas"]["Role"];

export type Session = {
  token: string;
  userId: string;
  role: Role;
  expiresAt: Date;
};

export const SESSION_COOKIE = "cic_session";

export const ROLES: readonly Role[] = [
  "ADMIN",
  "IT_MANAGER",
  "CHANGE_ENGINEER",
  "AGENT",
];

function isRole(value: unknown): value is Role {
  return ROLES.includes(value as Role);
}

function decodeBase64Url(value: string): string {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/");
  const bytes = Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function parseSession(
  token: string | undefined,
  now: Date = new Date(),
): Session | null {
  const payload = token?.split(".")[1];
  if (!token || !payload) return null;
  try {
    const claims: unknown = JSON.parse(decodeBase64Url(payload));
    if (typeof claims !== "object" || claims === null) return null;
    const { sub, role, exp } = claims as Record<string, unknown>;
    if (typeof sub !== "string" || !isRole(role) || typeof exp !== "number") {
      return null;
    }
    const expiresAt = new Date(exp * 1000);
    if (expiresAt <= now) return null;
    return { token, userId: sub, role, expiresAt };
  } catch {
    return null;
  }
}

function cookieAttributes(expiresAt: Date): string {
  const secure = location.protocol === "https:" ? "; Secure" : "";
  return `; Path=/; SameSite=Strict; Expires=${expiresAt.toUTCString()}${secure}`;
}

export function readSessionToken(): string | null {
  const entry = document.cookie
    .split("; ")
    .find((part) => part.startsWith(`${SESSION_COOKIE}=`));
  return entry ? entry.slice(SESSION_COOKIE.length + 1) : null;
}

export function readSessionCookie(): Session | null {
  return parseSession(readSessionToken() ?? undefined);
}

export function writeSessionCookie(token: string, expiresAt: Date): void {
  document.cookie = `${SESSION_COOKIE}=${token}${cookieAttributes(expiresAt)}`;
}

export function clearSessionCookie(): void {
  document.cookie = `${SESSION_COOKIE}=${cookieAttributes(new Date(0))}`;
}
