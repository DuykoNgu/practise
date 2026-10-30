import { NextResponse, type NextRequest } from "next/server";

import { resolveRedirect } from "@/lib/routes";
import { parseSession, SESSION_COOKIE } from "@/lib/session";

export function proxy(request: NextRequest) {
  const session = parseSession(request.cookies.get(SESSION_COOKIE)?.value);
  const target = resolveRedirect(
    request.nextUrl.pathname,
    session?.role ?? null,
  );
  if (!target) return NextResponse.next();
  return NextResponse.redirect(new URL(target, request.url));
}

export const config = {
  matcher: ["/((?!_next/|favicon.ico|.*\\..*).*)"],
};
