import sys
from dotenv import load_dotenv
from src.agents.orchestrator import Orchestrator

load_dotenv()

def main():
    orchestrator = Orchestrator()
    
    query = (
        sys.argv[1] if len(sys.argv) > 1 
        else "What was our CSAT performance in May 2026, and how does it compare to our target?"
    )
    
    print(f"\nAnalyzing Query: '{query}'...\n")
    response = orchestrator.run(query)
    
    print("=" * 60)
    print("NARRATIVE SUMMARY:")
    print("=" * 60)
    print(response.narrative_summary)
    print("\n" + "=" * 60)
    print("DATA METRICS USED:")
    print("=" * 60)
    print(response.data_metrics.model_dump_json(indent=2))
    print("\n" + "=" * 60)
    print("RETRIEVED FAQ CONTEXT:")
    print("=" * 60)
    for chunk in response.retrieved_context:
        print(f"[{chunk.chunk_id}] (Score: {chunk.relevance_score}):")
        print(chunk.content)
        print("-" * 40)

if __name__ == "__main__":
    main()