"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { adminApi, User } from "@/lib/api";

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.users().then((r) => setUsers(r.data)).catch(() => setError("Admin access required"));
    adminApi.stats().then((r) => setStats(r.data)).catch(() => {});
  }, []);

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Admin</h1>
      <p className="text-gray-500 mb-6">Platform-wide stats and user management.</p>

      {error && <div className="mb-6 text-sm text-amber-700 bg-amber-50 px-4 py-3 rounded-lg">{error}</div>}

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {Object.entries(stats).map(([k, v]) => (
            <div key={k} className="bg-white border border-gray-100 rounded-xl p-5">
              <div className="text-2xl font-semibold">{v}</div>
              <div className="text-sm text-gray-500 capitalize">{k.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white border border-gray-100 rounded-xl divide-y divide-gray-100">
        {users.map((u) => (
          <div key={u.id} className="px-4 py-3 flex items-center justify-between text-sm">
            <div>
              <div className="font-medium">{u.full_name || u.email}</div>
              <div className="text-xs text-gray-400">{u.email}</div>
            </div>
            {u.is_admin && <span className="text-xs bg-brand-50 text-brand-700 px-2 py-1 rounded-md">admin</span>}
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
