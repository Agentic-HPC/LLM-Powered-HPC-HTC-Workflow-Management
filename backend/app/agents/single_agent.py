"""
SingleAgent: the "single-agent" architecture referenced in the project
brief, contrasted against the multi-agent pipeline (Intent/Planning/
Execution/Analytics/Reporting as separate specialized agents).

A single LLM call does the reasoning that the multi-agent pipeline splits
across IntentAgent + PlanningAgent + ReportingAgent - one prompt is asked
to both interpret the request AND decide how to compute it. The actual
numeric computation still has to run as real code (an LLM can't reliably
do exact arithmetic over hundreds of rows), so this agent still calls the
same analytics_service functions - but there's exactly one "brain" making
every decision, no specialized planning/reporting stages, and no handoffs
between agents. This makes it directly comparable to the multi-agent run
on the same prompt: same dataset, same output shape, different
architecture and (usually) fewer, larger LLM calls.
"""
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.services import analytics_service
from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are a single AI agent responsible for an entire data
analysis task end-to-end: understanding the user's request, deciding what
computation to run, and writing the final report. You are not part of a
multi-agent pipeline - you make every decision yourself in one pass.

Given the user's request and a list of available datasets (with columns),
return ONLY a JSON object with this shape:
{
  "goal": "<one sentence description of what the user wants>",
  "dataset": "<name of the most relevant dataset>",
  "analysis_type": "<one of: summary, groupby, correlation>",
  "target_columns": ["<relevant column names>"],
  "group_by": "<column to group by, or null>"
}
"""

REPORT_SYSTEM_PROMPT = """You are the same single agent, now writing the
final report after your own computation has run. Write a concise markdown
summary (3-6 sentences) interpreting the results in plain language."""


class SingleAgent(BaseAgent):
    name = "single_agent"

    def __init__(self, db, log_callback=None):
        super().__init__(log_callback=log_callback)
        self.db = db

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.dataset import Dataset
        from app.services.dataset_service import load_dataset_df

        prompt = context["prompt"]
        datasets_meta = context.get("available_datasets", [])

        self.log("Single agent: interpreting request and choosing computation (1 LLM call)")
        decision_prompt = (
            f"User request: {prompt}\n\nAvailable datasets: {datasets_meta}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )
        decision = await llm_service.generate_json(decision_prompt, system=SYSTEM_PROMPT)
        self.log(f"Decision: {decision}")

        dataset = self.db.query(Dataset).filter(Dataset.name == decision.get("dataset")).first()
        if dataset is None:
            raise ValueError(f"Dataset '{decision.get('dataset')}' not found")

        self.log(f"Loading and analyzing dataset '{dataset.name}' directly (no separate DataAgent/AnalyticsAgent)")
        df = load_dataset_df(dataset).dropna(how="all")

        analysis_type = decision.get("analysis_type", "summary")
        if analysis_type == "groupby" and decision.get("group_by"):
            value_col = (decision.get("target_columns") or [None])[0]
            result = analytics_service.groupby_aggregate(df, decision["group_by"], value_col)
            chart_data = {"type": "bar", "data": result}
        elif analysis_type == "correlation":
            result = analytics_service.correlation_matrix(df)
            chart_data = {"type": "heatmap", "data": result}
        else:
            result = analytics_service.describe_dataframe(df)
            chart_data = {"type": "table", "data": result}

        self.log("Single agent: writing final report (2nd LLM call)")
        report_prompt = f"Original goal: {decision.get('goal')}\nComputed results (JSON): {result}\n\nWrite the report now."
        report_markdown = await llm_service.generate(report_prompt, system=REPORT_SYSTEM_PROMPT)

        context["intent"] = decision
        context["analytics_result"] = result
        context["analytics_action"] = analysis_type
        context["chart_data"] = chart_data
        context["report_markdown"] = report_markdown
        context["engine_metadata"] = {"engine": "single_agent", "llm_calls": 2}
        return context
