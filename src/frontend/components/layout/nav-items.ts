import { canAccess } from "@/lib/routes";
import type { Role } from "@/lib/session";

export type NavItem = { label: string; href: string };
export type NavGroup = { label: string; items: NavItem[] };

const NAV_GROUPS: readonly NavGroup[] = [
  {
    label: "Monitor",
    items: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Anomalies", href: "/anomalies" },
    ],
  },
  {
    label: "Records",
    items: [
      { label: "Changes", href: "/changes" },
      { label: "Tickets", href: "/tickets" },
    ],
  },
  {
    label: "Analysis",
    items: [{ label: "Baseline", href: "/baseline" }],
  },
  {
    label: "Administration",
    items: [
      { label: "Audit log", href: "/audit" },
      { label: "Settings", href: "/settings" },
      { label: "Users", href: "/users" },
    ],
  },
];

export function navGroupsFor(role: Role): NavGroup[] {
  return NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => canAccess(role, item.href)),
  })).filter((group) => group.items.length > 0);
}
