import { EmptyState } from "@/components/empty-state";

export default function DashboardPage() {
  return (
    <>
      <h1 className="mb-4 text-2xl font-semibold">Dashboard</h1>
      <EmptyState
        title="Nothing to show yet"
        description="The incident dashboard will appear here."
      />
    </>
  );
}
