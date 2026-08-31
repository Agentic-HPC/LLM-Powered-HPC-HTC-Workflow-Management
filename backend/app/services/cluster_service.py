"""
Simulated HPC/HTC cluster.

This does NOT talk to a real scheduler (Slurm/PBS/HTCondor). It models a
small fixed set of compute nodes with CPU/GPU/memory capacity, "assigns"
each job to whichever node currently looks least loaded, and generates a
believable resource-utilization time series while the job's pipeline runs -
so the platform can demonstrate job submission, resource tracking, and
CPU/GPU/hybrid execution modes as described in the project brief, without
requiring an actual cluster.
"""
import random
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.cluster_node import ClusterNode
from app.models.job import Job
from app.models.resource_usage import ResourceUsageSample

DEFAULT_NODES = [
    {"name": "cpu-node-01", "node_type": "cpu", "cpu_cores": 16, "gpu_count": 0, "memory_gb": 64},
    {"name": "cpu-node-02", "node_type": "cpu", "cpu_cores": 32, "gpu_count": 0, "memory_gb": 128},
    {"name": "gpu-node-01", "node_type": "gpu", "cpu_cores": 8, "gpu_count": 2, "memory_gb": 64},
    {"name": "hybrid-node-01", "node_type": "hybrid", "cpu_cores": 24, "gpu_count": 1, "memory_gb": 96},
]


def seed_cluster(db: Session) -> List[ClusterNode]:
    """Idempotently ensure the default simulated nodes exist."""
    existing_names = {n.name for n in db.query(ClusterNode).all()}
    created = []
    for spec in DEFAULT_NODES:
        if spec["name"] not in existing_names:
            node = ClusterNode(**spec)
            db.add(node)
            created.append(node)
    if created:
        db.commit()
        for n in created:
            db.refresh(n)
    return db.query(ClusterNode).all()


def pick_node(db: Session, prefer_gpu: bool = False) -> Optional[ClusterNode]:
    """Pick an idle node, preferring GPU-capable ones if the workload wants it."""
    nodes = seed_cluster(db)
    idle = [n for n in nodes if n.status == "idle"]
    pool = idle or nodes
    if prefer_gpu:
        gpu_nodes = [n for n in pool if n.gpu_count > 0]
        if gpu_nodes:
            pool = gpu_nodes
    return random.choice(pool) if pool else None


def mark_node_busy(db: Session, node: ClusterNode) -> None:
    node.status = "busy"
    db.commit()


def mark_node_idle(db: Session, node: ClusterNode) -> None:
    node.status = "idle"
    db.commit()


def record_usage_sample(
    db: Session, job: Job, node: Optional[ClusterNode], elapsed_seconds: float, stage: str,
    intensity: float = 1.0,
) -> ResourceUsageSample:
    """
    Generate one simulated resource reading. `intensity` (0-1+) scales how
    hard the stage is expected to hit CPU/memory - e.g. reduce/aggregation
    stages run hotter than a light data-load step.
    """
    base_cpu = min(95, 30 + intensity * 55 + random.uniform(-5, 5))
    base_mem = min(90, 20 + intensity * 40 + random.uniform(-5, 5))
    base_gpu = 0.0
    if node and node.gpu_count > 0 and intensity > 0.6:
        base_gpu = min(95, intensity * 70 + random.uniform(-5, 5))

    sample = ResourceUsageSample(
        job_id=job.id,
        node_id=node.id if node else None,
        elapsed_seconds=round(elapsed_seconds, 2),
        cpu_percent=round(max(0, base_cpu), 1),
        gpu_percent=round(max(0, base_gpu), 1),
        memory_percent=round(max(0, base_mem), 1),
        stage=stage,
    )
    db.add(sample)
    db.commit()
    return sample


def cluster_snapshot(db: Session) -> List[dict]:
    """Current state of all nodes, for the Cluster dashboard page."""
    nodes = seed_cluster(db)
    return [
        {
            "id": n.id,
            "name": n.name,
            "node_type": n.node_type,
            "cpu_cores": n.cpu_cores,
            "gpu_count": n.gpu_count,
            "memory_gb": n.memory_gb,
            "status": n.status,
        }
        for n in nodes
    ]
