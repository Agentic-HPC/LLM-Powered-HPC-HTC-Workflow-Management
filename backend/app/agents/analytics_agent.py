"""
AnalyticsAgent: runs the numerical/statistical work (summary stats,
group-by aggregation, time series resampling, correlation matrices) on the
DataFrame produced by DataAgent, using app.services.analytics_service.
"""
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.services import analytics_service


class AnalyticsAgent(BaseAgent):
    name = "analytics_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        step = context["current_step"]
        action = step["action"]
        params = step["params"]
        df = context["dataframe"]

        self.log(f"Running analytics action: {action} with params {params}")

        if action == "summary":
            result = analytics_service.describe_dataframe(df)
        elif action == "groupby_aggregate":
            result = analytics_service.groupby_aggregate(
                df, params["group_col"], params["value_col"]
            )
        elif action == "time_series":
            result = analytics_service.time_series(df, params["date_col"], params["value_col"])
        elif action == "correlation_matrix":
            result = analytics_service.correlation_matrix(df)
        else:
            raise ValueError(f"Unknown analytics action: {action}")

        self.log("Analytics step complete")
        context["analytics_result"] = result
        context["analytics_action"] = action
        return context
