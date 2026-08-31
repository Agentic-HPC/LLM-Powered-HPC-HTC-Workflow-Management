"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout } from "@/components/AppLayout";
import { datasetsApi, jobsApi, workflowsApi, promptsApi, Job, Workflow, Dataset } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function DashboardPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [llmOk, setLlmOk] = useState<boolean | null>(null);

  useEffect(() => {
    jobsApi.list().then((r) => setJobs(r.data)).catch(() => { });
    workflowsApi.list().then((r) => setWorkflows(r.data)).catch(() => { });
    datasetsApi.list().then((r) => setDatasets(r.data)).catch(() => { });
    promptsApi.llmHealth().then((r) => setLlmOk(!!r.data.reachable)).catch(() => setLlmOk(false));
  }, []);

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
      <p className="text-gray-500 mb-6">Overview of your workflows, jobs, and datasets.</p>

      <div className={`mb-6 px-4 py-3 rounded-lg text-sm ${llmOk ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}>
        {llmOk === null ? "Checking LLM connection..." : llmOk ? "LLM provider is connected and ready." : "LLM provider is not reachable — check your provider configuration."}
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Workflows" value={workflows.length} href="/workflows" />
        <StatCard label="Jobs" value={jobs.length} href="/jobs" />
        <StatCard label="Datasets" value={datasets.length} href="/datasets" />
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <h2 className="font-medium mb-3">Recent jobs</h2>
        {jobs.length === 0 && <p className="text-sm text-gray-400">No jobs yet. Start one from Prompt Studio.</p>}
        <div className="space-y-2">
          {jobs.slice(0, 5).map((j) => (
            <Link
              key={j.id}
              href={`/jobs/${j.id}`}
              className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 text-sm"
            >
              <span>Job #{j.id}</span>
              <StatusBadge status={j.status} />
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}

function StatCard({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link href={href} className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-sm transition-shadow">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </Link>
  );
}
