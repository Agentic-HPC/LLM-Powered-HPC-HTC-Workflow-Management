"""
ReportingAgent: the final pipeline stage. Takes the raw analytics_result
computed upstream and asks the LLM to write a short, plain-language
narrative summary (markdown), plus shapes the numeric result into a
chart-friendly structure for the frontend (Recharts-compatible arrays).
"""
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are the ReportingAgent in a data-analysis pipeline.
You receive the user's original goal and a JSON blob of computed analytics
results. Write a concise markdown report (3-6 sentences plus, if useful, a
short bulleted list of key findings). Do not restate raw JSON; interpret it
in plain language. Do not fabricate numbers not present in the data."""


class ReportingAgent(BaseAgent):
    name = "reporting_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        intent = context.get("intent", {})
        analytics_result = context["analytics_result"]
        analytics_action = context.get("analytics_action")

        self.log("Generating narrative report via LLM")

        user_prompt = (
            f"Original goal: {intent.get('goal')}\n"
            f"Analysis type: {analytics_action}\n"
            f"Computed results (JSON): {analytics_result}\n\n"
            "Write the markdown report now."
        )
        report_markdown = await llm_service.generate(user_prompt, system=SYSTEM_PROMPT)

        chart_data = self._shape_for_chart(analytics_action, analytics_result)

        self.log("Report generated")
        context["report_markdown"] = report_markdown
        context["chart_data"] = chart_data
        return context

    @staticmethod
    def _shape_for_chart(action: str, result: Any) -> Dict[str, Any]:
        if action in ("groupby_aggregate", "time_series") and isinstance(result, list):
            return {"type": "bar" if action == "groupby_aggregate" else "line", "data": result}
        if action == "correlation_matrix":
            return {"type": "heatmap", "data": result}
        return {"type": "table", "data": result}
