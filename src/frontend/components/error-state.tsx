import { Button } from "@/components/ui/button";

type ErrorStateProps = {
  title?: string;
  traceId?: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "We could not load this page",
  traceId,
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-2 rounded-lg border border-destructive/40 p-10 text-center"
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm text-muted-foreground">
        Try again in a moment. If it keeps happening, contact your
        administrator.
      </p>
      {traceId ? (
        <p className="text-xs text-muted-foreground">Reference: {traceId}</p>
      ) : null}
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}
