"""
PlanningAgent: converts the IntentAgent's structured intent into a concrete,
ordered list of executable steps that the ExecutionAgent will run. This is
also the shape saved to Workflow.definition so it can be replayed later.

If the job requested a Big Data processing paradigm (mapreduce/spark), the
analytics step is routed to that simulated engine instead of the plain
pandas AnalyticsAgent - but only for actions those engines support
(summary, groupby_aggregate); timeseries/correlation always run on pandas.
"""
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent

BIG_DATA_SUPPORTED_ACTIONS = {"summary", "groupby_aggregate"}


class PlanningAgent(BaseAgent):
    name = "planning_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        intent = context["intent"]
        paradigm = context.get("processing_paradigm", "pandas")
        self.log(f"Building execution plan from intent (paradigm={paradigm})")

        steps: List[Dict[str, Any]] = [
            {
                "agent": "data",
                "action": "load_dataset",
                "params": {"dataset": intent.get("dataset"), "n_partitions": 4},
            }
        ]

        analysis_type = intent.get("analysis_type", "summary")

        if analysis_type == "groupby":
            action, engine_params = "groupby_aggregate", {
                "group_col": intent.get("group_by"),
                "value_col": (intent.get("target_columns") or [None])[0],
            }
        elif analysis_type == "timeseries":
            action, engine_params = "time_series", {
                "date_col": intent.get("group_by"),
                "value_col": (intent.get("target_columns") or [None])[0],
            }
        elif analysis_type == "correlation":
            action, engine_params = "correlation_matrix", {}
        else:
            action, engine_params = "summary", {}

        use_big_data_engine = paradigm in ("mapreduce", "spark") and action in BIG_DATA_SUPPORTED_ACTIONS
        agent_key = paradigm if use_big_data_engine else "analytics"

        steps.append({"agent": agent_key, "action": action, "params": engine_params})

        steps.append({
            "agent": "reporting",
            "action": "generate_report",
            "params": {"output_format": intent.get("output_format", "narrative")},
        })

        self.log(f"Plan has {len(steps)} steps (analytics engine: {agent_key})")
        context["plan"] = steps
        return context
