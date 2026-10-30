import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Providers } from "@/app/providers";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { clearSessionCookie, writeSessionCookie } from "@/lib/session";
import { makeToken } from "../helpers";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ replace }),
}));

beforeEach(replace.mockClear);
afterEach(clearSessionCookie);

test("renders the page inside the shell with role-filtered navigation", async () => {
  writeSessionCookie(makeToken("AGENT"), new Date(Date.now() + 60_000));

  render(
    <Providers>
      <WorkspaceShell>
        <h1>Placeholder</h1>
      </WorkspaceShell>
    </Providers>,
  );

  expect(
    await screen.findByRole("heading", { name: "Placeholder" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Users" })).not.toBeInTheDocument();
});

test("log out clears the session and returns to login", async () => {
  writeSessionCookie(makeToken("ADMIN"), new Date(Date.now() + 60_000));
  render(
    <Providers>
      <WorkspaceShell>content</WorkspaceShell>
    </Providers>,
  );

  await userEvent.click(await screen.findByRole("button", { name: "Log out" }));

  expect(replace).toHaveBeenCalledWith("/login");
  expect(document.cookie).not.toContain("cic_session");
});

test("without a session it redirects to login and shows no content", async () => {
  render(
    <Providers>
      <WorkspaceShell>secret</WorkspaceShell>
    </Providers>,
  );

  await vi.waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
  expect(screen.queryByText("secret")).not.toBeInTheDocument();
});

test("an expired session signs the user out without a request", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "Date"] });
  writeSessionCookie(makeToken("ADMIN", 60), new Date(Date.now() + 60_000));
  render(
    <Providers>
      <WorkspaceShell>content</WorkspaceShell>
    </Providers>,
  );
  await vi.advanceTimersByTimeAsync(0);
  expect(screen.getByText("content")).toBeInTheDocument();

  await vi.advanceTimersByTimeAsync(61_000);

  expect(replace).toHaveBeenCalledWith("/login");
  vi.useRealTimers();
});
