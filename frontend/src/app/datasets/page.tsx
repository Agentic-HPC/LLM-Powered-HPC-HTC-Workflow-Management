"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { datasetsApi, Dataset } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);

  function load() {
    datasetsApi.list().then((r) => setDatasets(r.data));
  }

  useEffect(load, []);

  async function rescan() {
    setLoading(true);
    try {
      await datasetsApi.rescan();
      load();
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-semibold">Datasets</h1>
        <button
          onClick={rescan}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Rescan
        </button>
      </div>
      <p className="text-gray-500 mb-6">
        CSVs found in the backend&apos;s <code>data/</code> directory. Run <code>scripts/generate_datasets.py</code> to
        create sample data.
      </p>

      <div className="grid grid-cols-2 gap-4">
        {datasets.map((d) => (
          <div key={d.id} className="bg-white border border-gray-100 rounded-xl p-5">
            <div className="font-medium mb-1">{d.name}</div>
            <div className="text-xs text-gray-400 mb-3">{d.row_count} rows</div>
            <div className="flex flex-wrap gap-1">
              {(d.columns || []).map((c) => (
                <span key={c.name} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-md">
                  {c.name}
                </span>
              ))}
            </div>
          </div>
        ))}
        {datasets.length === 0 && <p className="text-sm text-gray-400">No datasets registered yet.</p>}
      </div>
    </AppLayout>
  );
}
