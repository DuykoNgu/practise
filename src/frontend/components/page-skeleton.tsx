import { Skeleton } from "@/components/ui/skeleton";

export function PageSkeleton() {
  return (
    <div role="status" aria-busy="true" className="flex flex-col gap-4">
      <span className="sr-only">Loading</span>
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}
