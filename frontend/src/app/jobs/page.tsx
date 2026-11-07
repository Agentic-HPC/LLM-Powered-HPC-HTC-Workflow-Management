"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout } from "@/components/AppLayout";
import { jobsApi, Job } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [restartingId, setRestartingId] = useState<number | null>(null);

  const fetchJobs = () => jobsApi.list().then((r) => setJobs(r.data));

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleRestart = async (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      setRestartingId(id);
      await jobsApi.restart(id);
      await fetchJobs();
    } catch (err: any) {
      alert("Failed to restart job: " + (err.response?.data?.detail || err.message));
    } finally {
      setRestartingId(null);
    }
  };

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Jobs</h1>
      <p className="text-gray-500 mb-6">Every pipeline run, live or historical.</p>

      <div className="bg-white border border-gray-100 rounded-xl divide-y divide-gray-100">
        {jobs.length === 0 && <div className="p-4 text-sm text-gray-400">No jobs yet.</div>}
        {jobs.map((j) => (
          <Link key={j.id} href={`/jobs/${j.id}`} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
            <div className="min-w-0 pr-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Job #{j.id}</span>
                {j.prompt && (
                  <span className="text-xs text-gray-500 truncate max-w-md italic">
                    &ldquo;{j.prompt}&rdquo;
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-400 flex items-center gap-2 mt-0.5">
                <span>{new Date(j.created_at).toLocaleString()}</span>
                <span className="bg-gray-100 px-1.5 py-0.5 rounded capitalize">
                  {j.architecture === "single_agent" ? "single-agent" : "multi-agent"}
                </span>
                <span className="bg-gray-100 px-1.5 py-0.5 rounded capitalize">{j.processing_paradigm}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-brand-500 transition-all duration-300" style={{ width: `${j.progress}%` }} />
              </div>
              <StatusBadge status={j.status} />
              <button
                onClick={(e) => handleRestart(e, j.id)}
                disabled={restartingId === j.id}
                title="Restart this job"
                className="text-xs px-2.5 py-1 rounded bg-gray-100 hover:bg-brand-50 hover:text-brand-700 text-gray-700 font-medium transition-colors disabled:opacity-50"
              >
                {restartingId === j.id ? "Restarting..." : "Restart"}
              </button>
            </div>
          </Link>
        ))}
      </div>
    </AppLayout>
  );
}
