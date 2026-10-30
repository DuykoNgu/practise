import Link from "next/link";

import { cn } from "@/lib/utils";
import { isUnder } from "@/lib/routes";
import type { Role } from "@/lib/session";
import { navGroupsFor } from "@/components/layout/nav-items";

type WorkspaceSidebarProps = { role: Role; activePath: string };

export function WorkspaceSidebar({ role, activePath }: WorkspaceSidebarProps) {
  return (
    <nav
      aria-label="Main"
      className="flex w-56 shrink-0 flex-col gap-6 overflow-y-auto border-r bg-sidebar p-4 text-sidebar-foreground"
    >
      {navGroupsFor(role).map((group) => (
        <section key={group.label} aria-labelledby={`nav-${group.label}`}>
          <h2
            id={`nav-${group.label}`}
            className="mb-2 px-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase"
          >
            {group.label}
          </h2>
          <ul className="flex flex-col gap-1">
            {group.items.map((item) => {
              const active = isUnder(activePath, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "block rounded-md px-2 py-1.5 text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
                      active
                        ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                        : "hover:bg-sidebar-accent/60",
                    )}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </nav>
  );
}
