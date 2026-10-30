import type { Role } from "@/lib/session";

function encode(value: object): string {
  return btoa(JSON.stringify(value))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export function makeToken(
  role: Role,
  expiresInSeconds = 1800,
  now: Date = new Date(),
): string {
  const exp = Math.floor(now.getTime() / 1000) + expiresInSeconds;
  return `${encode({ alg: "HS256" })}.${encode({ sub: "user-1", role, exp })}.signature`;
}
