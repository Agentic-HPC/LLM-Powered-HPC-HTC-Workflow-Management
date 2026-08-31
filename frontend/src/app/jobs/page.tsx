"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout } from "@/components/AppLayout";
import { jobsApi, Job } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    jobsApi.list().then((r) => setJobs(r.data));
    const interval = setInterval(() => jobsApi.list().then((r) => setJobs(r.data)), 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Jobs</h1>
      <p className="text-gray-500 mb-6">Every pipeline run, live or historical.</p>

      <div className="bg-white border border-gray-100 rounded-xl divide-y divide-gray-100">
        {jobs.length === 0 && <div className="p-4 text-sm text-gray-400">No jobs yet.</div>}
        {jobs.map((j) => (
          <Link key={j.id} href={`/jobs/${j.id}`} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
            <div>
              <div className="text-sm font-medium">Job #{j.id}</div>
              <div className="text-xs text-gray-400 flex items-center gap-2 mt-0.5">
                <span>{new Date(j.created_at).toLocaleString()}</span>
                <span className="bg-gray-100 px-1.5 py-0.5 rounded capitalize">
                  {j.architecture === "single_agent" ? "single-agent" : "multi-agent"}
                </span>
                <span className="bg-gray-100 px-1.5 py-0.5 rounded capitalize">{j.processing_paradigm}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-brand-500" style={{ width: `${j.progress}%` }} />
              </div>
              <StatusBadge status={j.status} />
            </div>
          </Link>
        ))}
      </div>
    </AppLayout>
  );
}
