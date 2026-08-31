"""
Orchestrator: wires together the full pipeline and persists progress/logs/
results against a Job row as it runs.

Two architecture modes (Job.architecture):
  - MULTI_AGENT:  IntentAgent -> PlanningAgent -> ExecutionAgent (Data ->
                  Analytics/MapReduce/Spark) -> ReportingAgent
  - SINGLE_AGENT: one SingleAgent does intent + computation + report

Two entry points:
  - run_prompt_pipeline(): ad-hoc, prompt -> ... -> report
  - run_workflow_pipeline(): replay a saved Workflow.definition directly
    (always multi-agent, since a saved plan already encodes agent routing)

Before running, a simulated cluster node is assigned to the job
(app.services.cluster_service) and released when the job finishes, and
resource-utilization samples are recorded as the pipeline executes.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.execution_agent import ExecutionAgent
from app.agents.intent_agent import IntentAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.single_agent import SingleAgent
from app.models.dataset import Dataset
from app.models.job import Job, JobArchitecture, JobStatus, ProcessingParadigm
from app.models.job_log import JobLog
from app.models.result import Result
from app.services import cluster_service


class Orchestrator:
    def __init__(self, db: Session, job: Job):
        self.db = db
        self.job = job

    def _persist_log(self, agent_name: str, message: str) -> None:
        entry = JobLog(job_id=self.job.id, agent_name=agent_name, message=message)
        self.db.add(entry)
        self.db.commit()

    def _persist_progress(self, pct: int) -> None:
        self.job.progress = pct
        self.db.commit()

    def _available_datasets_meta(self) -> List[Dict[str, Any]]:
        datasets = self.db.query(Dataset).all()
        return [{"name": d.name, "columns": d.columns} for d in datasets]

    def _assign_node(self) -> None:
        prefer_gpu = self.job.processing_paradigm in (ProcessingParadigm.MAPREDUCE, ProcessingParadigm.SPARK)
        node = cluster_service.pick_node(self.db, prefer_gpu=prefer_gpu)
        if node:
            cluster_service.mark_node_busy(self.db, node)
            self.job.node_id = node.id
            self.db.commit()
            self._persist_log("orchestrator", f"Assigned to simulated node '{node.name}' ({node.node_type})")

    def _release_node(self) -> None:
        if self.job.node_id:
            from app.models.cluster_node import ClusterNode
            node = self.db.query(ClusterNode).filter(ClusterNode.id == self.job.node_id).first()
            if node:
                cluster_service.mark_node_idle(self.db, node)

    async def _finalize(self, context: Dict[str, Any]) -> None:
        result = Result(
            job_id=self.job.id,
            metrics=context.get("analytics_result") if isinstance(context.get("analytics_result"), dict) else None,
            chart_data=context.get("chart_data"),
            report_markdown=context.get("report_markdown"),
            engine_metadata=context.get("engine_metadata"),
        )
        self.db.add(result)
        self.job.status = JobStatus.SUCCEEDED
        self.job.progress = 100
        self.job.finished_at = datetime.utcnow()
        self.db.commit()
        self._release_node()

    async def _fail(self, error: Exception) -> None:
        self.job.status = JobStatus.FAILED
        self.job.error_message = str(error)
        self.job.finished_at = datetime.utcnow()
        self.db.commit()
        self._persist_log("orchestrator", f"Job failed: {error}")
        self._release_node()

    async def run_prompt_pipeline(self, prompt: str) -> None:
        self.job.status = JobStatus.RUNNING
        self.job.started_at = datetime.utcnow()
        self.db.commit()
        self._assign_node()

        try:
            from app.models.cluster_node import ClusterNode
            node = self.db.query(ClusterNode).filter(ClusterNode.id == self.job.node_id).first() if self.job.node_id else None

            context: Dict[str, Any] = {
                "prompt": prompt,
                "available_datasets": self._available_datasets_meta(),
                "processing_paradigm": self.job.processing_paradigm.value,
            }

            if self.job.architecture == JobArchitecture.SINGLE_AGENT:
                self._persist_log("orchestrator", "Running SINGLE-AGENT architecture")
                single_agent = SingleAgent(db=self.db, log_callback=self._persist_log)
                context = await single_agent.run(context)
                self._persist_progress(90)
                cluster_service.record_usage_sample(
                    self.db, self.job, node, elapsed_seconds=1.0, stage="single_agent", intensity=0.8
                )
            else:
                self._persist_log("orchestrator", "Running MULTI-AGENT architecture")
                intent_agent = IntentAgent(log_callback=self._persist_log)
                context = await intent_agent.run(context)

                planning_agent = PlanningAgent(log_callback=self._persist_log)
                context = await planning_agent.run(context)

                execution_agent = ExecutionAgent(
                    db=self.db, log_callback=self._persist_log, progress_callback=self._persist_progress,
                    job=self.job, node=node,
                )
                context = await execution_agent.run(context)

            await self._finalize(context)
        except Exception as exc:  # noqa: BLE001
            await self._fail(exc)
            raise

    async def run_workflow_pipeline(self, plan: List[Dict[str, Any]], original_prompt: Optional[str] = None) -> None:
        self.job.status = JobStatus.RUNNING
        self.job.started_at = datetime.utcnow()
        self.db.commit()
        self._assign_node()

        try:
            from app.models.cluster_node import ClusterNode
            node = self.db.query(ClusterNode).filter(ClusterNode.id == self.job.node_id).first() if self.job.node_id else None

            context: Dict[str, Any] = {
                "prompt": original_prompt or "",
                "plan": plan,
                "intent": {"goal": original_prompt or "Replay saved workflow"},
                "processing_paradigm": self.job.processing_paradigm.value,
            }
            execution_agent = ExecutionAgent(
                db=self.db, log_callback=self._persist_log, progress_callback=self._persist_progress,
                job=self.job, node=node,
            )
            context = await execution_agent.run(context)
            await self._finalize(context)
        except Exception as exc:  # noqa: BLE001
            await self._fail(exc)
            raise
