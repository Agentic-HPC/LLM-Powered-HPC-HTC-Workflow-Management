"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppLayout } from "@/components/AppLayout";
import { workflowsApi, jobsApi, Workflow } from "@/lib/api";
import { Trash2, Play } from "lucide-react";

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);

  function load() {
    workflowsApi.list().then((r) => setWorkflows(r.data));
  }

  useEffect(load, []);

  async function run(id: number) {
    const resp = await jobsApi.create({ workflow_id: id });
    router.push(`/jobs/${resp.data.id}`);
  }

  async function remove(id: number) {
    await workflowsApi.remove(id);
    load();
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Workflows</h1>
      <p className="text-gray-500 mb-6">Saved, reusable analysis pipelines. Create new ones in Prompt Studio.</p>

      {workflows.length === 0 && (
        <p className="text-sm text-gray-400">No workflows yet.</p>
      )}

      <div className="space-y-3">
        {workflows.map((w) => (
          <div key={w.id} className="bg-white border border-gray-100 rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="font-medium">{w.name}</div>
              <div className="text-sm text-gray-500">{w.description || w.original_prompt}</div>
              <div className="text-xs text-gray-400 mt-1">{w.definition.length} steps</div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => run(w.id)}
                className="p-2 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100"
                title="Run"
              >
                <Play size={16} />
              </button>
              <button
                onClick={() => remove(w.id)}
                className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100"
                title="Delete"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
