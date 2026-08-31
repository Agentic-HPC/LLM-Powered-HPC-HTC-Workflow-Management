"""
IntentAgent: first stage of the pipeline. Takes the user's raw natural
language prompt (e.g. "show me average salary by department over the last
3 years") and uses the LLM to extract structured intent:
  - the analysis goal
  - which dataset(s) are relevant
  - what kind of output is wanted (chart, table, summary, forecast...)
"""
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are the IntentAgent in a data-analysis pipeline.
Given a user's natural language request and a list of available datasets
(with their columns), extract structured intent as JSON with this shape:

{
  "goal": "<one sentence description of what the user wants>",
  "dataset": "<name of the most relevant dataset>",
  "analysis_type": "<one of: summary, groupby, timeseries, correlation, forecast>",
  "target_columns": ["<column names relevant to the analysis>"],
  "group_by": "<column name to group by, or null>",
  "output_format": "<one of: chart, table, narrative>"
}
"""


class IntentAgent(BaseAgent):
    name = "intent_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context["prompt"]
        datasets_meta = context.get("available_datasets", [])

        self.log(f"Parsing intent from prompt: {prompt!r}")

        user_prompt = (
            f"User request: {prompt}\n\n"
            f"Available datasets: {datasets_meta}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )
        intent = await llm_service.generate_json(user_prompt, system=SYSTEM_PROMPT)

        self.log(f"Extracted intent: {intent}")
        context["intent"] = intent
        return context
