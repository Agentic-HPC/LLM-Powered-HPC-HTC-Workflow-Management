"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppLayout } from "@/components/AppLayout";
import { jobsApi, JobDetail } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function JobDetailPage() {
  const params = useParams();
  const jobId = Number(params.id);
  const [job, setJob] = useState<JobDetail | null>(null);
  const [restarting, setRestarting] = useState(false);

  const loadJob = useCallback(() => {
    if (!jobId) return;
    jobsApi.get(jobId).then((r) => setJob(r.data));
  }, [jobId]);

  useEffect(() => {
    loadJob();
    const interval = setInterval(() => {
      setJob((prev) => {
        if (prev && ["succeeded", "failed", "cancelled"].includes(prev.status)) {
          return prev;
        }
        loadJob();
        return prev;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [loadJob]);

  const handleRestart = async () => {
    if (!job) return;
    try {
      setRestarting(true);
      await jobsApi.restart(job.id);
      loadJob();
    } catch (err: any) {
      alert("Failed to restart job: " + (err.response?.data?.detail || err.message));
    } finally {
      setRestarting(false);
    }
  };

  if (!job) {
    return (
      <AppLayout>
        <p className="text-sm text-gray-400">Loading job...</p>
      </AppLayout>
    );
  }

  const chart = job.result?.chart_data;
  const engineMeta = job.result?.engine_metadata;

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-1">
        <div>
          <h1 className="text-2xl font-semibold">Job #{job.id}</h1>
          {job.prompt && (
            <p className="text-sm text-gray-500 mt-0.5 italic">
              &ldquo;{job.prompt}&rdquo;
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={job.status} />
          <button
            onClick={handleRestart}
            disabled={restarting}
            className="text-xs px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium transition-colors disabled:opacity-50 shadow-sm"
          >
            {restarting ? "Restarting..." : "Restart Job"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <Tag>{job.architecture === "single_agent" ? "Single-agent" : "Multi-agent"}</Tag>
        <Tag>{job.processing_paradigm}</Tag>
        {job.node_name && <Tag>node: {job.node_name}</Tag>}
        <span className="text-sm text-gray-400">Progress: {job.progress}%</span>
      </div>

      {job.error_message && (
        <div className="mb-6 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">{job.error_message}</div>
      )}

      {job.resource_samples.length > 0 && (
        <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6">
          <h2 className="font-medium mb-3">Simulated resource utilization</h2>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={job.resource_samples}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="elapsed_seconds" tickFormatter={(v) => `${v}s`} />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip formatter={(v: number) => `${v}%`} labelFormatter={(v) => `t=${v}s`} />
                <Legend />
                <Line type="monotone" dataKey="cpu_percent" name="CPU" stroke="#3d63dd" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="gpu_percent" name="GPU" stroke="#e07a3f" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="memory_percent" name="Memory" stroke="#22a06b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {engineMeta && (
        <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6">
          <h2 className="font-medium mb-3">Execution engine</h2>
          <div className="text-sm text-gray-600 mb-2">
            Engine: <span className="font-medium text-gray-800">{engineMeta.engine}</span>
            {engineMeta.partitions !== undefined && (
              <>
                {" "}
                · Partitions: <span className="font-medium text-gray-800">{engineMeta.partitions}</span>
              </>
            )}
            {engineMeta.llm_calls !== undefined && (
              <>
                {" "}
                · LLM calls: <span className="font-medium text-gray-800">{engineMeta.llm_calls}</span>
              </>
            )}
          </div>
          {engineMeta.stage_timings && (
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(engineMeta.stage_timings).map(([stage, timing]: [string, any]) => (
                <span key={stage} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-md font-mono">
                  {stage}: {Array.isArray(timing) ? `${timing.length} tasks` : `${timing}s`}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {chart && chart.type === "bar" && Array.isArray(chart.data) && chart.data.length > 0 && (
        <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6" style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={Object.keys(chart.data[0])[0]} />
              <YAxis />
              <Tooltip />
              <Bar dataKey={Object.keys(chart.data[0])[1]} fill="#3d63dd" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {chart && chart.type === "line" && Array.isArray(chart.data) && chart.data.length > 0 && (
        <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6" style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={Object.keys(chart.data[0])[0]} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey={Object.keys(chart.data[0])[1]} stroke="#3d63dd" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {job.result?.report_markdown && (
        <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6">
          <h2 className="font-medium mb-2">Report</h2>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{job.result.report_markdown}</p>
        </div>
      )}

      <div className="bg-white border border-gray-100 rounded-xl p-5">
        <h2 className="font-medium mb-3">Agent log</h2>
        <div className="space-y-2 font-mono text-xs">
          {job.logs.map((l, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-gray-400">{new Date(l.created_at).toLocaleTimeString()}</span>
              <span className="text-brand-600 font-semibold">[{l.agent_name}]</span>
              <span className="text-gray-700">{l.message}</span>
            </div>
          ))}
          {job.logs.length === 0 && <div className="text-gray-400">No logs yet.</div>}
        </div>
      </div>
    </AppLayout>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs font-medium bg-brand-50 text-brand-700 px-2 py-1 rounded-md capitalize">
      {children}
    </span>
  );
}
