import type { components } from "@/lib/api-types";
import { FORBIDDEN_PATH, LOGIN_PATH } from "@/lib/routes";
import { clearSessionCookie, readSessionCookie } from "@/lib/session";

export type ProblemDetails = components["schemas"]["ProblemDetails"];

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const LOGIN_REQUEST_PATH = "/auth/login";

const FALLBACK_PROBLEM: ProblemDetails = {
  title: "Something went wrong",
  status: 0,
  traceId: "",
};

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.title);
    this.name = "ApiError";
    this.status = problem.status;
    this.problem = problem;
  }
}

async function readProblem(response: Response): Promise<ProblemDetails> {
  const fallback = { ...FALLBACK_PROBLEM, status: response.status };
  try {
    const body = (await response.json()) as Partial<ProblemDetails>;
    if (typeof body.title !== "string") return fallback;
    return { ...fallback, ...body, status: response.status };
  } catch {
    return fallback;
  }
}

function leaveTo(path: string): void {
  if (location.pathname !== path) location.assign(path);
}

function handleAuthFailure(path: string, status: number): void {
  if (status === 401 && path !== LOGIN_REQUEST_PATH) {
    clearSessionCookie();
    leaveTo(LOGIN_PATH);
  } else if (status === 403) {
    leaveTo(FORBIDDEN_PATH);
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const merged = new Headers(headers);
  merged.set("Accept", "application/json, application/problem+json");
  const session = readSessionCookie();
  if (session) merged.set("Authorization", `Bearer ${session.token}`);
  if (json !== undefined) merged.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...rest,
      headers: merged,
      body: json === undefined ? rest.body : JSON.stringify(json),
    });
  } catch {
    throw new ApiError(FALLBACK_PROBLEM);
  }

  if (!response.ok) {
    handleAuthFailure(path, response.status);
    throw new ApiError(await readProblem(response));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
