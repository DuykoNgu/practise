import {
  clearSessionCookie,
  parseSession,
  readSessionCookie,
  writeSessionCookie,
} from "@/lib/session";
import { makeToken } from "../helpers";

afterEach(clearSessionCookie);

test("parses role and expiry from a valid token", () => {
  const session = parseSession(makeToken("IT_MANAGER"));
  expect(session?.role).toBe("IT_MANAGER");
  expect(session?.userId).toBe("user-1");
});

test.each([
  ["missing", undefined],
  ["malformed", "not-a-token"],
  ["expired", makeToken("ADMIN", -10)],
  ["unknown role", makeToken("ADMIN").replace(/\.[^.]+\./, ".e30.")],
])("rejects a %s token", (_name, token) => {
  expect(parseSession(token)).toBeNull();
});

test("round-trips through the cookie and clears it", () => {
  const token = makeToken("AGENT");
  writeSessionCookie(token, new Date(Date.now() + 60_000));
  expect(readSessionCookie()?.token).toBe(token);

  clearSessionCookie();
  expect(readSessionCookie()).toBeNull();
});
