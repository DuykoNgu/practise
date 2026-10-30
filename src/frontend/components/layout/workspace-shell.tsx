"use client";

import { usePathname } from "next/navigation";

import { PageSkeleton } from "@/components/page-skeleton";
import { WorkspaceSidebar } from "@/components/layout/workspace-sidebar";
import { WorkspaceTopbar } from "@/components/layout/workspace-topbar";
import { useSession } from "@/features/auth/hooks/use-session";

export function WorkspaceShell({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const { status, session, signOut } = useSession();

  if (status === "unauthenticated") return null;

  if (!session) {
    return (
      <div className="p-6">
        <PageSkeleton />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-background focus:p-2"
      >
        Skip to content
      </a>
      <WorkspaceTopbar role={session.role} onSignOut={signOut} />
      <div className="flex min-h-0 flex-1">
        <WorkspaceSidebar role={session.role} activePath={pathname} />
        <main id="main-content" className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
