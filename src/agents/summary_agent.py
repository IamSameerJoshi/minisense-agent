from google import genai
from google.genai import types

from src.schemas import SummaryAgentResult, SummaryTaskSpec


class SummaryAgent:
    """Generates a grounded executive narrative from typed agent results."""

    def __init__(self, client: genai.Client, model_name: str):
        self.name = "SummaryAgent"
        self.client = client
        self.model_name = model_name

    def execute(self, task_spec: SummaryTaskSpec) -> SummaryAgentResult:
        context_text = "\n\n".join(
            f"[{chunk.chunk_id}]: {chunk.content}"
            for chunk in task_spec.rag_result.retrieved_chunks
        )
        comparison_text = (
            task_spec.comparison_result.model_dump_json()
            if task_spec.comparison_result
            else "No period comparison was requested."
        )
        prompt = f"""
You are MiniSense, an executive survey analyst. Answer the user's business question.

Ground your response strictly in the provided structured results and Business FAQ Context.
Do NOT invent numbers or targets, and do not perform new calculations. Present the answer
as a concise, professional executive narrative paragraph.

User Question:
{task_spec.question}

Survey Metrics (computed deterministically):
{task_spec.data_result.model_dump_json()}

Period Comparison (computed deterministically):
{comparison_text}

Business FAQ Context:
{context_text}
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return SummaryAgentResult(
            narrative=response.text.strip(),
            supporting_chunk_ids=[
                chunk.chunk_id
                for chunk in task_spec.rag_result.retrieved_chunks
            ],
        )