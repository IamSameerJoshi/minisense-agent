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

class ComparisonTaskSpec(BaseModel):
    """Structured instruction for comparing two survey periods."""
    current_start: str = Field(..., description="Current period start date (YYYY-MM-DD)")
    current_end: str = Field(..., description="Current period end date (YYYY-MM-DD)")
    previous_start: str = Field(..., description="Previous period start date (YYYY-MM-DD)")
    previous_end: str = Field(..., description="Previous period end date (YYYY-MM-DD)")
    business_id: Optional[str] = Field(None, description="Optional business ID filter")

class SummaryTaskSpec(BaseModel):
    """Structured input for the final narrative synthesis."""
    question: str
    data_result: "DataAgentResult"
    rag_result: "RAGAgentResult"
    comparison_result: Optional["ComparisonResult"] = None

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

class ComparisonResult(BaseModel):
    """Structured period-over-period analysis returned by the ComparisonAgent."""
    current_metrics: DataAgentResult
    previous_metrics: DataAgentResult
    average_rating_delta: float
    response_count_delta: int
    theme_changes: dict[str, int]
    direction: Literal["improved", "declined", "unchanged"]

class SummaryAgentResult(BaseModel):
    """Structured narrative returned by the SummaryAgent."""
    narrative: str
    supporting_chunk_ids: List[str] = Field(default_factory=list)

# --- 3. Final Synthesis Output ---

class OrchestratorResponse(BaseModel):
    """Final answer synthesized by the Orchestrator for the user."""
    question: str
    narrative_summary: str
    data_metrics: Optional[DataAgentResult] = None
    comparison_metrics: Optional[ComparisonResult] = None
    retrieved_context: Optional[List[RetrievedChunk]] = None