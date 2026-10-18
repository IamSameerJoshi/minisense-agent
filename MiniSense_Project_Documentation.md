# MiniSense: Survey Intelligence Agent

## 1. Project overview

MiniSense is an agentic business-intelligence project built to answer operational questions from customer survey data and business policy documents. The core idea was simple: instead of asking a large language model to directly reason over raw survey rows, we split the work into two reliable layers:

- a deterministic data layer for calculations and trend extraction
- a retrieval layer for operational policies and business targets

This architecture makes the answers more trustworthy, more explainable, and more aligned with real business decisions.

The project is framed around GreenLeaf Bistro, a fictional restaurant brand. It ingests a large synthetic survey dataset, retrieves policy context from an FAQ, and synthesizes a final executive answer grounded in both numbers and business rules.

---

## 2. Why this project exists

The original problem was that customer feedback is often noisy, unstructured, and spread across multiple sources:

- customer ratings
- free-text feedback
- service policies
- target KPIs such as CSAT thresholds
- escalation rules and refund procedures

If we use an LLM in a naive way, it may do one or more of the following:

- hallucinate numeric results
- misinterpret business targets
- fail to explain where the answer came from
- generate confident summaries without verifying policy context

In a real business scenario, this is dangerous because executives need decisions backed by evidence. We wanted to create a system that behaves more like a small analytics team than a generic chatbot.

So the motivation was:

- keep metrics precise and auditable
- ground responses in company policies
- make the final answer explainable to a non-technical stakeholder
- keep the architecture modular and interview-friendly

---

## 3. The core design decision: separate analytics from reasoning

One of the most important decisions in this project was to avoid putting raw survey records into the LLM prompt.

Instead, we built a pipeline where:

1. the orchestrator identifies the user’s intent
2. a data agent computes survey metrics through deterministic code
3. a retrieval agent searches the FAQ and business rules
4. a final synthesizer combines both results into a concise answer

This is a critical design principle:

- arithmetic and filtering should be executed by code with a clear, testable logic path
- semantic reasoning should be done using retrieved evidence, not by making the model “guess” at metrics

This reduces error risk and makes the answer not just generated, but grounded.

---

## 4. High-level architecture

The project follows a layered agentic pattern.

### 4.1 Orchestrator Agent

The orchestrator is the brain of the system. It takes the user’s business question and converts it into structured tasks for downstream agents.

It performs two key responsibilities:

- creates a structured `DataTaskSpec` for analytics
- creates a structured `RAGTaskSpec` for FAQ retrieval

After the sub-agents return their results, the orchestrator synthesizes the final narrative.

Why this matters:

- it keeps the workflow modular
- it allows a clean contract between the planner and workers
- it reduces prompt brittleness by always routing tasks through typed schemas

### 4.2 Data Agent

This component is responsible for business metrics such as:

- total responses
- average rating
- CSAT score
- rating distribution
- top complaint themes

It calls a deterministic metrics function implemented in Python using Polars.

This choice was intentional. Polars is excellent for large tabular datasets, fast filtering, and arithmetic. It gives us reliable metrics on a large synthetic dataset without relying on the LLM for numeric calculation.

### 4.3 RAG Agent

The retrieval agent speaks to a local ChromaDB vector store that contains the GreenLeaf Bistro FAQ and operating policy documents.

The idea was to answer questions like:

- what is the CSAT target?
- what is the escalation procedure?
- what are the operational thresholds?

The agent retrieves relevant chunks and passes them to the orchestrator for synthesis.

### 4.4 Typed schemas

The schemas in `src/schemas.py` define the contracts between components. This is a strong engineering decision because it gives us:

- structured inputs and outputs
- validation before execution
- clearer boundaries between agents
- easier debugging and future extension

Rather than passing plain untyped dictionaries around, we use Pydantic models for:

- task specification for analytics
- task specification for retrieval
- metric outputs
- retrieved FAQ chunks
- final orchestrator response

This is a classic reliability pattern in LLM applications: treat the model as a planner, but keep the execution layer strict and typed.

### 4.5 The two alternative agents from the assignment

The assignment listed four possible sub-agent roles and required at least two.
This project implemented the DataAgent and RAGAgent. The other two roles could
have been developed as a ComparisonAgent and a SummaryAgent.

#### ComparisonAgent

The ComparisonAgent would compare two periods, such as April and May, and
surface meaningful changes in customer experience. It would receive a typed
`ComparisonTaskSpec` containing:

- the current period's start and end dates
- the previous period's start and end dates
- an optional business ID filter

Rather than recalculating metrics itself, the agent would call the existing
DataAgent twice: once with a `DataTaskSpec` for the current period and once for
the previous period. It would then deterministically calculate the differences
between the two `DataAgentResult` objects.

A typed `ComparisonResult` could include:

- current and previous metric results
- the average-rating or CSAT delta
- the response-count delta
- the change in each theme count
- a direction such as `improved`, `declined`, or `unchanged`

For example, for the question “How did May compare with April?”, the
orchestrator would create the two date ranges, the ComparisonAgent would run
the DataAgent for both ranges, and the final result would identify whether
ratings, response volume, or complaint themes had changed. Keeping these
calculations in Python preserves the project's rule that the LLM should not do
arithmetic over raw survey records.

#### SummaryAgent

The SummaryAgent would own the final narrative-writing step that is currently
implemented by `Orchestrator.synthesize_narrative()`. It would receive a typed
`SummaryTaskSpec` containing:

- the original user question
- the `DataAgentResult`
- an optional `ComparisonResult`
- the `RAGAgentResult` with retrieved FAQ context

The agent would use Gemini to express those supplied results as a concise
executive paragraph. Its prompt would require it to use only the structured
metrics and retrieved FAQ content, avoid inventing values, and distinguish
calculated survey results from documented business policy. It would return a
typed `SummaryAgentResult` containing the narrative and the IDs of the FAQ
chunks used as supporting context.

The alternative end-to-end workflow would therefore be:

```text
User question
	|
Orchestrator
	|--------> DataAgent
	|--------> ComparisonAgent ----> DataAgent for current period
	|                              `-> DataAgent for previous period
	|--------> RAGAgent
	`--------> SummaryAgent
			  |
		 Executive narrative
```

To implement these roles, `src/schemas.py` would define
`ComparisonTaskSpec`, `ComparisonResult`, `SummaryTaskSpec`, and
`SummaryAgentResult`. New `comparison_agent.py` and `summary_agent.py` modules
would implement the agents' `execute()` methods. The orchestrator planner
would return the additional task specification when a question requires a
period comparison, execute the comparison and retrieval work, and pass all
structured results to SummaryAgent. The existing narrative method could then
be moved into SummaryAgent.

This design would provide a clearer separation between computation,
period-over-period analysis, document retrieval, and narrative generation. The
two agents are described here as a proposed extension; they are not currently
implemented in this repository.

---

## 5. What we built in the project

### 5.1 Survey data pipeline

The synthetic data generator creates approximately 60,000 survey records from April to May 2026.

Why this dataset matters:

- it is large enough to mimic realistic operational volume
- it includes a natural decline in quality during May, reflecting a business issue
- it includes text patterns that align with ratings and service themes

The generator intentionally creates subtle shifts in sentiment:

- April has generally stronger satisfaction
- May shows a downturn with more low ratings and wait-time complaints

This makes the agent’s analysis realistic and meaningful. It also allows us to demonstrate that the system can reason about business performance changes across time.

### 5.2 FAQ and policy indexing

The `product_faq.txt` file contains structured Q/A entries about:

- popular menu items
- average wait time targets
- food quality escalation rules
- service complaint handling
- CSAT targets
- peak-hour patterns
- loyalty rewards and mobile ordering

These items are chunked and then indexed into ChromaDB. The key decision was to split the content into atomic Q/A blocks instead of indexing the entire document as one giant block.

Why this is important:

- retrieval becomes more precise
- a query can match a specific policy item rather than a broad unrelated context block
- the final answer is easier to attribute back to a source document

### 5.3 Deterministic metrics logic

The metrics tool computes business KPIs using Polars. We used explicit date filtering and rating logic to compute:

- average rating
- rating distribution by star value
- total response count
- theme counts based on phrase matching

The theme extraction is simple but effective for a focused demo. It tracks phrases like:

- wait / delay / minute
- avocado / bowl / fresh / cold
- clean / bussing

This is a practical compromise: a lightweight lexical extractor is transparent and explainable, which is better than passing unstructured text directly to the LLM for sentiment classification.

### 5.4 Agent execution flow

The operational flow is:

1. User asks a question
2. Orchestrator plans the task using Gemini
3. DataAgent computes metrics from the dataset
4. RAGAgent retrieves relevant policy chunks from FAQ
5. Orchestrator synthesizes an answer grounded in both sources

This is more powerful than a single prompt because each step has a clear role and responsibility.

---

## 6. Why we made certain technology choices

### 6.1 Gemini for planning and synthesis

We used Gemini as the reasoning layer for:

- converting natural language to structured task specs
- summarizing the final answer into an executive narrative

This is a good fit because it gives us strong language understanding and natural summarization, while still keeping the numeric work in code.

The important design decision is that Gemini is not asked to compute the data; it is asked to plan and explain.

### 6.2 Polars for analytics

Polars was chosen because it is fast, memory-efficient, and expressive for data transformations.

The reason it matters here is that survey data is not small. We intentionally generate large-scale records, so the data layer must be efficient and deterministic.

### 6.3 ChromaDB for retrieval

ChromaDB is a lightweight and practical vector store for local experimentation.

We used a persistent local Chroma collection so that:

- the retrieval database can be rebuilt on demand
- the project works without a cloud search service
- the FAQ/operational knowledge remains grounded and repeatable

The trade-off is that it is a simple retrieval system, not a full enterprise knowledge graph. But for this demo, it is exactly the right level of complexity.

### 6.4 Pydantic models for structured contracts

This is one of the most important engineering choices in the project.

Using Pydantic:

- validates outputs before they reach downstream steps
- makes the system easier to debug
- ensures the orchestrator and agents communicate with stable interfaces
- creates a clean boundary between model-generated content and deterministic code

This reduces the common failure mode in AI apps where unstructured model output breaks the rest of the pipeline.

---

## 7. Why this system is useful in real business settings

This project is not just a toy example. It mirrors a common business need:

- data analysts get a large volume of customer feedback
- operations teams need answers to practical questions
- leaders want a grounded narrative, not a generic AI response

The system is helpful because it combines two things:

- quantitative truth from data
- policy truth from internal documents

This is the right pattern for questions like:

- Why did our CSAT drop in May?
- Which issue is most common in customer feedback?
- What should we do according to policy when customer wait times exceed the threshold?
- Which operational program can help reduce wait-time burden?

In many organizations, those decisions require both numbers and procedure. This project captures exactly that combination.

---

## 8. The specific business insight demonstrated by the project

A key demonstration in the project is that May’s performance dropped materially below the company target.

The FAQ defines a target CSAT of 4.5 or higher, and a below-4.0 threshold that mandates a root-cause review. The system is designed to compare actual survey performance against those rules.

This is valuable because it shows the workflow is not just summarizing comments; it is turning customer experience data into operational action.

The broader lesson is:

- customer feedback is useful only when connected to an operational threshold
- an AI system becomes valuable when it converts raw sentiment into action-oriented insight

---

## 9. Key trade-offs and design philosophy

### 9.1 Reliability over cleverness

We chose clear, explainable logic over overly complex prompting patterns. This is a deliberate philosophy. A business-facing AI system must be reliable before it is impressive.

### 9.2 Determinism over improvisation

When the system calculates metrics, it should not rely on model estimates. We used real code for that logic.

### 9.3 Agentic but bounded

The project is agentic in that different parts are responsible for different tasks, but it is still bounded by strong contracts and structured outputs.

This is important because pure open-ended LLM workflows can be hard to trust. Here, the system is orchestrated, not chaotic.

### 9.3 Local-first implementation

The project is designed to run locally with a persistent vector store and local dataset. This makes it easy to prototype, test, and explain in interviews or demos without depending on a full cloud infrastructure stack.

---

## 10. What we learned from this implementation

This project teaches a few practical lessons about AI system design:

- LLMs are best used as planners and synthesizers, not as calculators
- retrieval matters when policy context is important
- structured schemas are essential for reliable multi-step agent workflows
- business value comes from combining data and operational context, not from raw text generation alone
- a small, modular system can often outperform an over-engineered demo if it is clear and grounded

---

## 11. Future improvements

If this project were extended into production, the next steps would likely be:

- add a real business dashboard interface
- introduce stronger theme classification models instead of simple keyword matching
- add regional or store-level analysis
- expand the FAQ knowledge base beyond one file
- incorporate monitoring and evaluation pipelines for retrieval quality
- move from local Chroma to a more scalable vector infrastructure

The current version is intentionally simple and explainable, which makes it a strong interview and prototyping project.

---

## 12. Interview-ready summary

If I had to explain this project in one sentence, I would say:

> MiniSense is a grounded survey intelligence system that combines deterministic analytics with retrieval-based policy grounding to answer business questions from customer feedback in an explainable and operationally useful way.

And the motivation is:

> We wanted to avoid the common problem where AI gives plausible but unverified answers. By separating metrics, policies, and synthesis, we created a system that is more reliable, more interpretable, and more suited to real business decision-making.

---

## 13. Edge cases and questions an interviewer may ask

This project is interview-friendly because it is not just a simple chatbot. It has real architecture decisions, concrete trade-offs, and known limitations. Interviewers often push on edge cases and failure modes. Here are the most likely questions and how to answer them intelligently.

### 13.1 What happens if the user asks a question that cannot be answered from the FAQ?

This is a realistic edge case. The system may retrieve irrelevant or weak context if the query is vague, indirect, or uses terminology outside the document.

Example:

- user asks: "How do we reduce stress during busy periods?"
- the FAQ uses terms like "weekend brunch peak hours", "mobile ordering", and "priority pickup"

The answer may be weaker because the retrieval layer depends on semantic similarity.

What we would do in production:

- add a fallback path when top-k scores are low
- ask a clarifying question when the intent is ambiguous
- expand the query with synonyms or domain vocabulary
- trigger a confidence threshold and refuse to answer with strong claims

This is a good answer because it shows awareness that retrieval is not magical and needs guardrails.

### 13.2 What if the FAQ retrieval returns the wrong policy chunk?

This is an important failure mode. The project intentionally avoids letting the model make up policy details, but retrieval can still miss the right document or pull a nearby but incorrect one.

Examples of wrong retrieval:

- returning a general FAQ item instead of the actual escalation rule
- retrieving a loyalty program policy for a wait-time question
- confusing food quality and service complaint procedures

The mitigation is:

- improve document chunking granularity
- use higher-quality embeddings or alternative retrieval methods
- rerank the top candidates before synthesis
- add business-specific metadata filters such as category, issue type, and policy type

This is a strong interview point because it shows that you understand the difference between a retrieval system working and a retrieval system being production-safe.

### 13.3 Why not let the LLM directly compute the CSAT instead of using Polars?

This is a very likely question.

The answer is that numerical metrics should be deterministic and auditable. A model can estimate or miscount values when the dataset is large and the task is repetitive. In a business context, that is unacceptable.

Why code is better here:

- it avoids arithmetic hallucination
- it makes metrics reproducible
- it gives transparent logic for auditing and debugging
- it keeps the model focused on reasoning and summarization, not counting

This is one of the strongest design justifications in the project.

### 13.4 What if the survey data has missing values or malformed entries?

In a real dataset, rows can be incomplete, contain nulls, or have inconsistent date formats.

The current project assumes clean synthetic data, but a production version would need:

- validation before metric computation
- safe handling of null ratings or null free-text
- date parsing with error handling
- dropping or logging malformed records
- exposing data-quality warnings to the system output

This is a good interview answer because it shows you think beyond the prototype and understand production data hygiene.

### 13.5 What if the business asks for a date range outside the dataset coverage?

The data covers April 1 to May 31, 2026. If the user asks for a different time range, we need a clean response.

The system should:

- filter to available dates
- report zero results or a clear no-data explanation
- avoid fabricating performance numbers outside the dataset

This is a practical and important edge case because many user questions will not line up exactly with the training or source data.

### 13.6 How would you handle a multi-intent query?

Example:

- "What was our CSAT in May, which complaints drove it, and what should we do according to policy?"

This is a tough query because it combines analytics, operational issue analysis, and policy retrieval.

A robust system would:

- decompose the query into sub-questions
- route metrics and policy tasks separately
- collect evidence for each part before synthesis
- summarize with distinct sections or logic blocks

This is also a useful answer because it shows you understand the challenge of multi-intent reasoning in agentic systems.

### 13.7 What are the limitations of keyword-based theme extraction?

The project uses simple phrase matching for complaint themes. This is transparent and easy to explain, but it has weaknesses:

- synonyms are missed
- wording variations are not normalized
- sentiment is inferred poorly where language is ambiguous
- sarcasm and subtle complaints can be missed

A more advanced version could use:

- a small classification model
- embedding-based clustering of themes
- dictionary normalization and stemming
- human-reviewed labeling for business-specific categories

This makes a strong technical answer because it shows you know the difference between a prototype and a production-ready insight engine.

### 13.8 How would you evaluate whether the system is actually good?

A good answer should move beyond "it works on my sample" and mention evaluation.

Possible evaluation dimensions:

- retrieval precision: did we retrieve the correct FAQ chunk?
- answer groundedness: did the final narrative cite the right evidence?
- metric accuracy: do the numbers match the data exactly?
- query robustness: how does the system behave on ambiguous or indirect prompts?

In this project, the repository includes evaluation-style examples in [eval_samples.md](eval_samples.md), which is a strong sign of being thoughtful about quality and debugging.

### 13.9 Why is the architecture not just a single LLM prompt?

Interviewers often ask this because they want to see whether you understand the architecture trade-off.

The answer:

- a single prompt is simple, but brittle
- it mixes reasoning with data operations
- it becomes hard to debug and hard to audit
- it fails when the user asks for precise numeric business answers

Our design keeps responsibilities separate, which gives better control and more trustworthy outputs.

### 13.10 What would you do differently in a production system?

This is a standard follow-up question.

A thoughtful answer would include:

- add eval sets and regression tests
- use a stricter retrieval reranker
- move from local Chroma to a more scalable vector store
- add metrics governance and alerting
- support store-level and location-level filtering
- introduce explicit confidence scores and abstention when evidence is weak

This shows maturity and indicates you understand that prototypes and production systems are very different.

### 13.11 What is the biggest risk in this design?

The biggest risk is not the LLM itself; it is the mismatch between the generated answer and real business evidence.

In other words:

- retrieval can fail silently
- models can sound confident while being wrong
- policy references may be underspecified or misinterpreted
- business users may trust the output too much without checking the source evidence

A real solution would add:

- source traceability
- confidence thresholds
- citations or chunk references in the final output
- explicit separation between facts, assumptions, and recommendations

This is an excellent interview answer because it reflects practical engineering judgment.

### 13.12 How would you explain the project in one sentence for an interview?

A concise, strong answer is:

> I built a grounded survey intelligence agent that separates deterministic business metrics from retrieval-based policy context so the final answer is explainable, auditable, and relevant to operational decisions.

This captures both the technical and business value of the project in one line.

---

## 14. Final takeaway

This project demonstrates a practical AI architecture for enterprise-style analytics. The most important design principle is that the system should not ask a language model to do numerical reasoning and policy interpretation in one uncontrolled step.

Instead, it should:

- calculate with code
- retrieve with evidence
- explain with context
- decide with grounded business logic

That is the core idea behind MiniSense, and it is the strongest technical story behind the project.

---

## 15. Interview confidence checklist

If you are preparing for the interview, focus on these points:

- the project solves a real business problem with grounded answers
- we separate deterministic computation from LLM reasoning
- we use typed schemas for stable interfaces and validation
- retrieval is evidence-based, not just model-generated
- we are aware of failure modes and trade-offs
- the system has a modular architecture that can be extended in production

If you can speak clearly about these points, the interview will feel much more like a technical systems discussion than a simple demo review.
