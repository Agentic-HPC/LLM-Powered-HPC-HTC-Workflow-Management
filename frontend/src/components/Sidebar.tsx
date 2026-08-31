"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, Sparkles, Workflow, ListChecks, Database, Server, ShieldCheck, LogOut } from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/store/auth-store";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/prompt-studio", label: "Prompt Studio", icon: Sparkles },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/jobs", label: "Jobs", icon: ListChecks },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/cluster", label: "Cluster", icon: Server },
  { href: "/admin", label: "Admin", icon: ShieldCheck },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const email = useAuthStore((s) => s.email);

  return (
    <aside className="w-64 shrink-0 border-r border-gray-200 bg-white h-screen sticky top-0 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="font-semibold text-lg text-brand-700">HPC/HTC AI</div>
        <div className="text-xs text-gray-400">Multi-agent analysis platform</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname === href
                ? "bg-brand-50 text-brand-700"
                : "text-gray-600 hover:bg-gray-100"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-3 py-4 border-t border-gray-100">
        <div className="px-3 text-xs text-gray-400 mb-2 truncate">{email}</div>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="flex items-center gap-2 px-3 py-2 w-full rounded-lg text-sm text-gray-600 hover:bg-gray-100"
        >
          <LogOut size={16} /> Sign out
        </button>
      </div>
    </aside>
  );
}
