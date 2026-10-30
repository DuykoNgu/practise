import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { PageSkeleton } from "@/components/page-skeleton";

test("the skeleton announces loading", () => {
  render(<PageSkeleton />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading");
});

test("the empty state explains itself and offers an action", () => {
  render(
    <EmptyState
      title="No tickets"
      description="Import some."
      action={<button>Import</button>}
    />,
  );
  expect(
    screen.getByRole("heading", { name: "No tickets" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Import" })).toBeInTheDocument();
});

test("the error state shows only a trace reference and retries", async () => {
  const onRetry = vi.fn();
  render(<ErrorState traceId="abc-123" onRetry={onRetry} />);

  expect(screen.getByRole("alert")).toHaveTextContent("Reference: abc-123");
  await userEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(onRetry).toHaveBeenCalledOnce();
});
