from src.schemas import RAGTaskSpec, RAGAgentResult
from src.rag.retriever import retrieve_faq_context

class RAGAgent:
    """
    Sub-agent responsible for retrieving relevant chunks from the Product FAQ.
    Grounds business answers in company targets, timelines, and policies.
    """
    def __init__(self):
        self.name = "RAGAgent"

    def execute(self, task_spec: RAGTaskSpec) -> RAGAgentResult:
        """
        Queries the vector store using the structured task specification.
        """
        return retrieve_faq_context(task_spec)