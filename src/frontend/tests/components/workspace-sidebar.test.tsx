import { render, screen } from "@testing-library/react";

import { WorkspaceSidebar } from "@/components/layout/workspace-sidebar";
import type { Role } from "@/lib/session";

function labels(role: Role): string[] {
  render(<WorkspaceSidebar role={role} activePath="/dashboard" />);
  return screen.getAllByRole("link").map((link) => link.textContent ?? "");
}

test("an administrator sees every page", () => {
  expect(labels("ADMIN")).toEqual([
    "Dashboard",
    "Anomalies",
    "Changes",
    "Tickets",
    "Baseline",
    "Audit log",
    "Settings",
    "Users",
  ]);
});

test("an IT manager sees the audit log but not settings or users", () => {
  const items = labels("IT_MANAGER");
  expect(items).toContain("Audit log");
  expect(items).not.toContain("Settings");
  expect(items).not.toContain("Users");
});

test.each(["CHANGE_ENGINEER", "AGENT"] as const)(
  "%s sees no administration group",
  (role) => {
    labels(role);
    expect(screen.queryByText("Administration")).not.toBeInTheDocument();
    expect(screen.getByText("Records")).toBeInTheDocument();
  },
);

test("marks the current page for assistive technology", () => {
  render(<WorkspaceSidebar role="AGENT" activePath="/anomalies/7" />);
  expect(screen.getByRole("link", { name: "Anomalies" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute(
    "aria-current",
  );
});
