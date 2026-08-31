"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppLayout } from "@/components/AppLayout";
import { promptsApi, workflowsApi, jobsApi } from "@/lib/api";

export default function PromptStudioPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [architecture, setArchitecture] = useState<"multi_agent" | "single_agent">("multi_agent");
  const [paradigm, setParadigm] = useState<"pandas" | "mapreduce" | "spark">("pandas");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ intent: any; plan: any[] } | null>(null);

  async function handleParse() {
    setError(null);
    setLoading(true);
    setPreview(null);
    try {
      const resp = await promptsApi.parse(prompt);
      setPreview(resp.data as any);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
        "Could not reach the configured LLM provider. Check the provider configuration and API key."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleRunNow() {
    setLoading(true);
    try {
      const resp = await jobsApi.create({ prompt, architecture, processing_paradigm: paradigm });
      router.push(`/jobs/${resp.data.id}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveWorkflow() {
    if (!preview) return;
    const name = window.prompt("Name this workflow:", prompt.slice(0, 40));
    if (!name) return;
    await workflowsApi.create({
      name,
      definition: preview.plan,
      original_prompt: prompt,
    });
    router.push("/workflows");
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Prompt Studio</h1>
      <p className="text-gray-500 mb-6">
        Describe what you want in plain language. The IntentAgent and PlanningAgent will turn it
        into an executable plan.
      </p>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="e.g. Show me average salary by department, and how it's changed over time"
        rows={4}
        className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 mb-4"
      />

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Agent architecture</label>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
            <ToggleButton
              active={architecture === "multi_agent"}
              onClick={() => setArchitecture("multi_agent")}
              label="Multi-agent"
            />
            <ToggleButton
              active={architecture === "single_agent"}
              onClick={() => setArchitecture("single_agent")}
              label="Single-agent"
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {architecture === "multi_agent"
              ? "Intent → Planning → Data → Analytics → Reporting, as separate specialized agents."
              : "One agent handles interpretation, computation, and reporting in a single pass."}
          </p>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Processing paradigm</label>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
            <ToggleButton active={paradigm === "pandas"} onClick={() => setParadigm("pandas")} label="Pandas" />
            <ToggleButton
              active={paradigm === "mapreduce"}
              onClick={() => setParadigm("mapreduce")}
              label="MapReduce"
            />
            <ToggleButton active={paradigm === "spark"} onClick={() => setParadigm("spark")} label="Spark" />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {paradigm === "pandas"
              ? "Single in-memory computation (HPC-style)."
              : `Simulated ${paradigm === "mapreduce" ? "Hadoop MapReduce" : "Spark"}: dataset is partitioned and processed in distributed-style stages (HTC/Big Data-style). Best for summary/groupby prompts.`}
          </p>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <button
          onClick={handleParse}
          disabled={!prompt || loading}
          className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? "Thinking..." : "Preview plan"}
        </button>
        <button
          onClick={handleRunNow}
          disabled={!prompt || loading}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          Run now
        </button>
      </div>

      {error && <div className="mb-6 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">{error}</div>}

      {preview && (
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h2 className="font-medium mb-3">Proposed plan</h2>
          <div className="text-sm text-gray-600 mb-4">
            <span className="font-medium text-gray-800">Goal:</span> {preview.intent.goal}
          </div>
          <ol className="space-y-2 mb-4">
            {preview.plan.map((step, i) => (
              <li key={i} className="flex items-center gap-3 text-sm px-3 py-2 bg-gray-50 rounded-lg">
                <span className="w-5 h-5 flex items-center justify-center rounded-full bg-brand-100 text-brand-700 text-xs font-medium">
                  {i + 1}
                </span>
                <code className="text-xs text-gray-700">
                  {step.agent}.{step.action}({JSON.stringify(step.params)})
                </code>
              </li>
            ))}
          </ol>
          <button
            onClick={handleSaveWorkflow}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Save as workflow
          </button>
        </div>
      )}
    </AppLayout>
  );
}

function ToggleButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 px-3 py-2 font-medium transition-colors ${active ? "bg-brand-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
        }`}
    >
      {label}
    </button>
  );
}
