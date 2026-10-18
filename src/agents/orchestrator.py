import os
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from src.schemas import (
    DataTaskSpec,
    RAGTaskSpec,
    DataAgentResult,
    RAGAgentResult,
    OrchestratorResponse,
    ComparisonTaskSpec,
    ComparisonResult,
    SummaryTaskSpec,
)
from src.agents.data_agent import DataAgent
from src.agents.rag_agent import RAGAgent
from src.agents.comparison_agent import ComparisonAgent
from src.agents.summary_agent import SummaryAgent

# Internal schema for Gemini's structured planning step
class AgentPlan(BaseModel):
    data_spec: DataTaskSpec = Field(description="Plan parameters for the survey metrics tool")
    rag_spec: RAGTaskSpec = Field(description="Search parameters for the FAQ vector store")
    comparison_spec: Optional[ComparisonTaskSpec] = Field(
        default=None,
        description="Period comparison parameters, or null when no comparison is needed",
    )

class Orchestrator:
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.data_agent = DataAgent()
        self.rag_agent = RAGAgent()
        self.comparison_agent = ComparisonAgent(self.data_agent)
        self.summary_agent = SummaryAgent(self.client, self.model_name)

    def plan_tasks(self, user_query: str) -> AgentPlan:
        """
        Translates a natural language question into typed task specs using Gemini.
        """
        prompt = f"""
You are the planner for MiniSense, an AI survey intelligence system.
Analyze the user question and determine the sub-agent task parameters.

Constraints:
- The survey dataset spans from 2026-04-01 to 2026-05-31.
- 'data_spec' extracts start_date, end_date (YYYY-MM-DD or null), and metrics to compute.
- 'rag_spec' defines the semantic search query and top_k to check business targets/policies.
- 'comparison_spec' is required only when the user asks to compare two periods. It must
    contain explicit current and previous date ranges; otherwise set it to null.

User Question: "{user_query}"
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AgentPlan,
                temperature=0.0
            )
        )

        plan = AgentPlan.model_validate_json(response.text)
        return plan

    def synthesize_narrative(
        self,
        user_query: str,
        data_result: DataAgentResult,
        rag_result: RAGAgentResult,
        comparison_result: Optional[ComparisonResult] = None,
    ) -> str:
        """
        Produces a grounded executive narrative through the SummaryAgent.
        """
        result = self.summary_agent.execute(
            SummaryTaskSpec(
                question=user_query,
                data_result=data_result,
                rag_result=rag_result,
                comparison_result=comparison_result,
            )
        )
        return result.narrative

    def run(self, user_query: str) -> OrchestratorResponse:
        """
        Full orchestration flow:
        1. Plan task specs with Gemini
        2. Execute DataAgent, optional ComparisonAgent, and RAGAgent
        3. Synthesize the narrative through SummaryAgent
        """
        plan = self.plan_tasks(user_query)

        data_result = self.data_agent.execute(plan.data_spec)
        comparison_result = (
            self.comparison_agent.execute(plan.comparison_spec)
            if plan.comparison_spec
            else None
        )
        rag_result = self.rag_agent.execute(plan.rag_spec)

        narrative = self.synthesize_narrative(
            user_query,
            data_result,
            rag_result,
            comparison_result,
        )

        return OrchestratorResponse(
            question=user_query,
            narrative_summary=narrative,
            data_metrics=data_result,
            comparison_metrics=comparison_result,
            retrieved_context=rag_result.retrieved_chunks
        )