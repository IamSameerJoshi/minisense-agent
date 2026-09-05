from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date

# --- 1. Task Specifications (Orchestrator -> Sub-Agents) ---

class DataTaskSpec(BaseModel):
    """Structured task instruction sent to the DataAgent."""
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    metrics_to_compute: List[Literal["csat", "average_rating", "response_count", "top_themes"]] = Field(
        default=["csat", "average_rating", "response_count"],
        description="Explicit list of metrics the agent must calculate"
    )
    business_id: Optional[str] = Field(None, description="Optional filter by business ID")

class RAGTaskSpec(BaseModel):
    """Structured query instruction sent to the RAGAgent."""
    query: str = Field(..., description="Semantic search query for the business FAQ/policy")
    top_k: int = Field(default=3, description="Number of context chunks to retrieve")

# --- 2. Structured Outputs (Sub-Agents -> Orchestrator) ---

class ThemeFrequency(BaseModel):
    theme: str
    count: int
    sentiment: Literal["positive", "negative", "neutral"]

class DataAgentResult(BaseModel):
    """Structured response returned by the DataAgent."""
    total_responses: int
    csat_score: float = Field(..., description="% of 4 and 5 star ratings, or average CSAT out of 5")
    average_rating: float
    rating_distribution: dict[int, int]
    top_themes: List[ThemeFrequency] = Field(default_factory=list)

class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    relevance_score: float

class RAGAgentResult(BaseModel):
    """Structured response returned by the RAGAgent."""
    query: str
    retrieved_chunks: List[RetrievedChunk]

# --- 3. Final Synthesis Output ---

class OrchestratorResponse(BaseModel):
    """Final answer synthesized by the Orchestrator for the user."""
    question: str
    narrative_summary: str
    data_metrics: Optional[DataAgentResult] = None
    retrieved_context: Optional[List[RetrievedChunk]] = None