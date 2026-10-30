import { ApiError, apiFetch } from "@/lib/api-client";
import { clearSessionCookie, writeSessionCookie } from "@/lib/session";
import { makeToken } from "../helpers";

const assign = vi.fn();

function respond(
  status: number,
  body?: unknown,
  contentType = "application/json",
) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": contentType },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
  vi.spyOn(window, "location", "get").mockReturnValue({
    ...window.location,
    pathname: "/dashboard",
    assign,
  });
  assign.mockClear();
});

afterEach(() => {
  clearSessionCookie();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test("sends the JWT as a bearer token and returns the body", async () => {
  const token = makeToken("ADMIN");
  writeSessionCookie(token, new Date(Date.now() + 60_000));
  vi.mocked(fetch).mockResolvedValue(respond(200, { ok: true }));

  const result = await apiFetch<{ ok: boolean }>("/dashboard");

  expect(result).toEqual({ ok: true });
  const headers = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Headers;
  expect(headers.get("Authorization")).toBe(`Bearer ${token}`);
});

test("sends JSON bodies with a content type", async () => {
  vi.mocked(fetch).mockResolvedValue(respond(204));

  await apiFetch("/auth/logout", { method: "POST", json: { a: 1 } });

  const init = vi.mocked(fetch).mock.calls[0]?.[1];
  expect(init?.body).toBe('{"a":1}');
  expect((init?.headers as Headers).get("Content-Type")).toBe(
    "application/json",
  );
});

test("401 clears the session, goes to login, and raises the problem", async () => {
  writeSessionCookie(makeToken("ADMIN"), new Date(Date.now() + 60_000));
  vi.mocked(fetch).mockResolvedValue(
    respond(
      401,
      { title: "Authentication required", status: 401, traceId: "t-1" },
      "application/problem+json",
    ),
  );

  await expect(apiFetch("/dashboard")).rejects.toMatchObject({ status: 401 });

  expect(assign).toHaveBeenCalledWith("/login");
  expect(document.cookie).not.toContain("cic_session");
});

test("403 goes to the forbidden page and keeps the session", async () => {
  writeSessionCookie(makeToken("AGENT"), new Date(Date.now() + 60_000));
  vi.mocked(fetch).mockResolvedValue(
    respond(
      403,
      { title: "Access denied", status: 403, traceId: "t-2" },
      "application/problem+json",
    ),
  );

  await expect(apiFetch("/settings")).rejects.toBeInstanceOf(ApiError);

  expect(assign).toHaveBeenCalledWith("/forbidden");
  expect(document.cookie).toContain("cic_session");
});

test("exposes problem+json fields including field errors and trace id", async () => {
  vi.mocked(fetch).mockResolvedValue(
    respond(
      400,
      {
        title: "Invalid input",
        status: 400,
        traceId: "t-3",
        errors: { email: ["Required"] },
      },
      "application/problem+json",
    ),
  );

  const error = await apiFetch("/users", { method: "POST" }).catch(
    (e: unknown) => e,
  );

  expect(error).toBeInstanceOf(ApiError);
  expect((error as ApiError).problem.errors).toEqual({ email: ["Required"] });
  expect((error as ApiError).problem.traceId).toBe("t-3");
  expect(assign).not.toHaveBeenCalled();
});

test("a non-JSON failure becomes a generic problem with the status", async () => {
  vi.mocked(fetch).mockResolvedValue(new Response("<html>", { status: 502 }));

  await expect(apiFetch("/dashboard")).rejects.toMatchObject({
    status: 502,
    problem: { title: "Something went wrong" },
  });
});

test("a network failure becomes a generic problem", async () => {
  vi.mocked(fetch).mockRejectedValue(new TypeError("offline"));

  await expect(apiFetch("/dashboard")).rejects.toMatchObject({ status: 0 });
});

test("a rejected login keeps the user on the form instead of redirecting", async () => {
  vi.mocked(fetch).mockResolvedValue(
    respond(
      401,
      { title: "Authentication required", status: 401, traceId: "t-4" },
      "application/problem+json",
    ),
  );

  await expect(
    apiFetch("/auth/login", { method: "POST" }),
  ).rejects.toMatchObject({ status: 401 });

  expect(assign).not.toHaveBeenCalled();
});
