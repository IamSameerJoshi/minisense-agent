import os
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from src.schemas import (
    DataTaskSpec,
    RAGTaskSpec,
    DataAgentResult,
    RAGAgentResult,
    OrchestratorResponse
)
from src.agents.data_agent import DataAgent
from src.agents.rag_agent import RAGAgent

# Internal schema for Gemini's structured planning step
class AgentPlan(BaseModel):
    data_spec: DataTaskSpec = Field(description="Plan parameters for the survey metrics tool")
    rag_spec: RAGTaskSpec = Field(description="Search parameters for the FAQ vector store")

class Orchestrator:
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.data_agent = DataAgent()
        self.rag_agent = RAGAgent()

    def plan_tasks(self, user_query: str) -> tuple[DataTaskSpec, RAGTaskSpec]:
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
        return plan.data_spec, plan.rag_spec

    def synthesize_narrative(
        self,
        user_query: str,
        data_result: DataAgentResult,
        rag_result: RAGAgentResult
    ) -> str:
        """
        Produces a grounded executive narrative combining computed data and retrieved policy chunks.
        """
        context_text = "\n\n".join([f"[{c.chunk_id}]: {c.content}" for c in rag_result.retrieved_chunks])

        prompt = f"""
You are MiniSense, an executive survey analyst. Answer the user's business question.

Ground your response strictly in the provided Survey Metrics and Business FAQ Context.
Do NOT invent numbers or targets. Present the answer as a concise, professional executive narrative paragraph.

User Question:
{user_query}

Survey Metrics (Computed deterministically):
- Total Responses: {data_result.total_responses}
- CSAT / Average Rating: {data_result.average_rating} / 5.0
- Rating Distribution: {data_result.rating_distribution}
- Top Themes: {[t.model_dump() for t in data_result.top_themes]}

Business FAQ Context:
{context_text}
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text.strip()

    def run(self, user_query: str) -> OrchestratorResponse:
        """
        Full orchestration flow:
        1. Plan task specs with Gemini
        2. Execute sub-agents (DataAgent + RAGAgent)
        3. Synthesize narrative answer with Gemini
        """
        data_spec, rag_spec = self.plan_tasks(user_query)

        data_result = self.data_agent.execute(data_spec)
        rag_result = self.rag_agent.execute(rag_spec)

        narrative = self.synthesize_narrative(user_query, data_result, rag_result)

        return OrchestratorResponse(
            question=user_query,
            narrative_summary=narrative,
            data_metrics=data_result,
            retrieved_context=rag_result.retrieved_chunks
        )