import { canAccess, resolveRedirect } from "@/lib/routes";

test("visitors are sent to login, except on the login page", () => {
  expect(resolveRedirect("/dashboard", null)).toBe("/login");
  expect(resolveRedirect("/login", null)).toBeNull();
});

test("signed-in users skip the login page and land on the dashboard", () => {
  expect(resolveRedirect("/login", "AGENT")).toBe("/dashboard");
  expect(resolveRedirect("/", "AGENT")).toBe("/dashboard");
});

test.each([
  ["/settings", "IT_MANAGER", "/forbidden"],
  ["/users", "AGENT", "/forbidden"],
  ["/audit", "CHANGE_ENGINEER", "/forbidden"],
  ["/tickets/import", "CHANGE_ENGINEER", "/forbidden"],
  ["/settings", "ADMIN", null],
  ["/audit", "IT_MANAGER", null],
  ["/tickets/import", "AGENT", null],
  ["/anomalies/42", "AGENT", null],
] as const)("%s as %s resolves to %s", (path, role, expected) => {
  expect(resolveRedirect(path, role)).toBe(expected);
});

test("a path prefix is not mistaken for a restricted route", () => {
  expect(canAccess("AGENT", "/users-guide")).toBe(true);
});
