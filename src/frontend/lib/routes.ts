import { ROLES, type Role } from "@/lib/session";

export const LOGIN_PATH = "/login";
export const FORBIDDEN_PATH = "/forbidden";
export const HOME_PATH = "/dashboard";

const ROUTE_ROLES: readonly (readonly [string, readonly Role[]])[] = [
  ["/tickets/import", ["ADMIN", "IT_MANAGER", "AGENT"]],
  ["/audit", ["ADMIN", "IT_MANAGER"]],
  ["/settings", ["ADMIN"]],
  ["/users", ["ADMIN"]],
];

export function isUnder(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

export function rolesAllowedOn(pathname: string): readonly Role[] {
  const match = ROUTE_ROLES.find(([prefix]) => isUnder(pathname, prefix));
  return match ? match[1] : ROLES;
}

export function canAccess(role: Role, pathname: string): boolean {
  return rolesAllowedOn(pathname).includes(role);
}

export function resolveRedirect(
  pathname: string,
  role: Role | null,
): string | null {
  if (isUnder(pathname, LOGIN_PATH)) return role ? HOME_PATH : null;
  if (!role) return LOGIN_PATH;
  if (pathname === "/") return HOME_PATH;
  return canAccess(role, pathname) ? null : FORBIDDEN_PATH;
}
