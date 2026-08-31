"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { clusterApi, ClusterNode } from "@/lib/api";
import { Cpu, MonitorSmartphone } from "lucide-react";

export default function ClusterPage() {
  const [nodes, setNodes] = useState<ClusterNode[]>([]);

  useEffect(() => {
    function load() {
      clusterApi.nodes().then((r) => setNodes(r.data));
    }
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold mb-1">Cluster</h1>
      <p className="text-gray-500 mb-6">
        Simulated HPC/HTC compute nodes. Jobs are assigned to an idle node when they run; MapReduce/Spark jobs prefer
        GPU-capable nodes.
      </p>

      <div className="grid grid-cols-2 gap-4">
        {nodes.map((n) => (
          <div key={n.id} className="bg-white border border-gray-100 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 font-medium">
                {n.node_type === "gpu" ? <MonitorSmartphone size={16} /> : <Cpu size={16} />}
                {n.name}
              </div>
              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${
                  n.status === "idle" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                }`}
              >
                {n.status}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs text-gray-500">
              <div>
                <div className="text-base font-semibold text-gray-800">{n.cpu_cores}</div>
                CPU cores
              </div>
              <div>
                <div className="text-base font-semibold text-gray-800">{n.gpu_count}</div>
                GPUs
              </div>
              <div>
                <div className="text-base font-semibold text-gray-800">{n.memory_gb}GB</div>
                Memory
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-400 capitalize">type: {n.node_type}</div>
          </div>
        ))}
        {nodes.length === 0 && <p className="text-sm text-gray-400">Loading cluster...</p>}
      </div>
    </AppLayout>
  );
}
