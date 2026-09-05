# Part 2: RAG Pipeline Evaluation Checkpoint

This document records the evaluation of the document retrieval and synthesis pipeline across 3 representative business questions grounded in the GreenLeaf Bistro FAQ.

---

### Question 1: Operational Policy Thresholds
* **User Query:** *"What was our CSAT performance in May 2026, and how does it compare to our target?"*[cite: 1]
* **Retrieved Chunks:**
  * `[faq_chunk_005]` (Relevance: 0.537):  
    > "Q: What is your official CSAT target?  
    > A: GreenLeaf Bistro maintains a company-wide target CSAT score of 4.5 or higher (on a 1 to 5 scale). Monthly location scores between 4.0 and 4.4 require a weekly store management check-in. Any store or period dropping below a 4.0 CSAT automatically triggers a mandatory root-cause review with the regional operations team to address staffing, kitchen throughput, or inventory gaps."
  * `[faq_chunk_002]` (Relevance: 0.199):  
    > "Q: What is your average wait time for orders?  
    > A: We target an average preparation time of under 10 minutes for walk-in counter orders during standard off-peak hours. Peak hours (12:00 PM – 1:30 PM lunch and 6:00 PM – 8:00 PM dinner), prep times may increase to 15–20 minutes..."
* **Final Synthesized Answer:**  
  In May 2026, GreenLeaf Bistro recorded an average CSAT score of 3.27 out of 5.0 across 30,315 survey responses. This performance falls significantly below the company-wide target of 4.5 and drops beneath the critical 4.0 operational threshold. According to company policy, this triggers a mandatory root-cause review with the regional operations team to investigate underlying operational bottlenecks.
* **Retrieval Commentary:**  
  * **What worked well:** Exact semantic alignment on core concepts ("CSAT", "target") allowed ChromaDB to rank the policy clause (`faq_chunk_005`) as the top result with high confidence.
  * **Shortcomings:** The second chunk (`faq_chunk_002`) had low relevance (~0.20), serving as minor background rather than directly answering the target threshold.

---

### Question 2: Complaint Handling & Escalation Protocols
* **User Query:** *"What are customers complaining about most in May, and what is our escalation procedure?"*
* **Retrieved Chunks:**
  * `[faq_chunk_004]` (Relevance: 0.492):  
    > "Q: How are service complaints handled?  
    > A: Complaints regarding staff behavior, excessive wait times, or cleanliness are logged directly into our internal Guest Care portal. Managers conduct an end-of-shift review for all logged tickets. If a service delay exceeds 25 minutes without prior staff notification, the customer's beverage is comped on the spot."
  * `[faq_chunk_003]` (Relevance: 0.441):  
    > "Q: How do you handle customer complaints regarding food quality?  
    > A: Any quality issue, such as incorrect temperature, incorrect ingredients, or dietary mismatches, is escalated to the shift manager within 15 minutes of reporting. The customer is immediately offered either an instant replacement prepared with priority status or a full refund back to their original payment method, plus a 15% discount voucher for their next visit."
* **Final Synthesized Answer:**  
  Customer survey feedback for May highlights "Wait Time / Delays" as the predominant negative driver (8,324 mentions). GreenLeaf Bistro's operational procedure dictates that wait time and service complaints must be recorded in the internal Guest Care portal for end-of-shift review. Furthermore, if a customer experiences a service delay exceeding 25 minutes without prior notification, floor staff are mandated to comp the customer's beverage immediately.
* **Retrieval Commentary:**  
  * **What worked well:** Both relevant complaint resolution protocols were retrieved, giving the synthesizer the complete policy picture across service and quality.
  * **Shortcomings:** The vector search lacks negative filtering. Because the question was broad ("complaints"), it retrieved food quality protocols alongside service delays, leaving disambiguation entirely to the synthesis stage.

---

### Question 3: Peak Capacity & Existing Mitigation Programs
* **User Query:** *"How can we alleviate counter delays during weekend peak hours using existing programs?"*
* **Retrieved Chunks:**
  * `[faq_chunk_008]` (Relevance: 0.228):  
    > "Q: How does the loyalty rewards program work?  
    > A: Guests enrolled in the GreenLeaf Perks program earn 10 points for every dollar spent. Points can be redeemed for complimentary beverages, bakery items, or meal discounts. Members also receive priority ordering during peak hours via the mobile application."
  * `[faq_chunk_006]` (Relevance: 0.215):  
    > "Q: What are your operational hours and peak dining times?  
    > A: All urban locations are open Monday through Sunday from 7:00 AM to 9:00 PM. Weekend brunch between 10:00 AM and 2:00 PM accounts for our highest table turnover and longest dining durations, often reaching full seating capacity."
* **Final Synthesized Answer:**  
  To alleviate congestion during weekend brunch peak hours (10:00 AM – 2:00 PM), management should steer guests toward the GreenLeaf Perks loyalty program. Members receive priority mobile ordering, which bypasses counter order lines and spreads kitchen throughput more predictably.
* **Retrieval Commentary:**  
  * **What worked well:** Successfully matched the operational challenge (peak hour delays) with a program incentive (loyalty mobile ordering).
  * **Shortcomings:** When a query describes a solution abstractly ("existing programs") without naming the entity ("loyalty" or "Perks"), semantic similarity scores drop to ~0.22. A strict relevance threshold cutoff might have prematurely discarded the loyalty chunk.
