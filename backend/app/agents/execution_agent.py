"""
ExecutionAgent: iterates over the plan built by PlanningAgent and routes
each step to the correct specialized agent (data / analytics / mapreduce /
spark / reporting), updating job progress as it goes. If a Job and
ClusterNode are supplied, it also records simulated resource-utilization
samples after each step so the frontend can chart CPU/GPU/memory usage
over the run - this is what stands in for real HPC/HTC resource tracking.
"""
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.data_agent import DataAgent
from app.agents.mapreduce_agent import MapReduceAgent
from app.agents.spark_agent import SparkAgent
from app.agents.reporting_agent import ReportingAgent
from app.models.cluster_node import ClusterNode
from app.models.job import Job
from app.services import cluster_service

# Roughly how "hard" each stage hits simulated resources (0-1), used to
# shape the fake CPU/GPU/memory curve reported to the frontend.
STAGE_INTENSITY = {
    "data": 0.35,
    "analytics": 0.75,
    "mapreduce": 0.9,
    "spark": 0.85,
    "reporting": 0.5,
}


class ExecutionAgent(BaseAgent):
    name = "execution_agent"

    def __init__(
        self, db: Session, log_callback=None, progress_callback=None,
        job: Optional[Job] = None, node: Optional[ClusterNode] = None,
    ):
        super().__init__(log_callback=log_callback)
        self.db = db
        self.job = job
        self.node = node
        self._progress_callback = progress_callback
        self._agents = {
            "data": DataAgent(db=db, log_callback=log_callback),
            "analytics": AnalyticsAgent(log_callback=log_callback),
            "mapreduce": MapReduceAgent(log_callback=log_callback),
            "spark": SparkAgent(log_callback=log_callback),
            "reporting": ReportingAgent(log_callback=log_callback),
        }

    def _report_progress(self, pct: int) -> None:
        if self._progress_callback:
            self._progress_callback(pct)

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        plan = context["plan"]
        total = len(plan)
        start_time = time.perf_counter()

        for i, step in enumerate(plan, start=1):
            agent_key = step["agent"]
            agent = self._agents.get(agent_key)
            if agent is None:
                raise ValueError(f"No executor registered for agent '{agent_key}'")

            self.log(f"Step {i}/{total}: {agent_key}.{step['action']}")
            context["current_step"] = step
            context = await agent.run(context)

            if self.job is not None:
                elapsed = time.perf_counter() - start_time
                intensity = STAGE_INTENSITY.get(agent_key, 0.5)
                cluster_service.record_usage_sample(
                    self.db, self.job, self.node, elapsed_seconds=elapsed,
                    stage=f"{agent_key}.{step['action']}", intensity=intensity,
                )

            self._report_progress(int(i / total * 90))  # reserve last 10% for finalization

        return context
