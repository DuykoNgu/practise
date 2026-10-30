import Link from "next/link";
import { LogOut, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { viewerTimeZone } from "@/lib/format";
import type { Role } from "@/lib/session";

const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Administrator",
  IT_MANAGER: "IT Manager",
  CHANGE_ENGINEER: "Change Engineer",
  AGENT: "Agent",
};

type WorkspaceTopbarProps = { role: Role; onSignOut: () => void };

export function WorkspaceTopbar({ role, onSignOut }: WorkspaceTopbarProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
      <span className="font-semibold">
        {process.env.NEXT_PUBLIC_APP_NAME ?? "CIC"}
      </span>
      <div className="flex items-center gap-3 text-sm">
        <span className="text-muted-foreground">
          Times shown in {viewerTimeZone()}
        </span>
        <span>{ROLE_LABELS[role]}</span>
        <Button asChild variant="ghost" size="sm">
          <Link href="/profile">
            <UserRound aria-hidden="true" />
            Profile
          </Link>
        </Button>
        <Button variant="outline" size="sm" onClick={onSignOut}>
          <LogOut aria-hidden="true" />
          Log out
        </Button>
      </div>
    </header>
  );
}
