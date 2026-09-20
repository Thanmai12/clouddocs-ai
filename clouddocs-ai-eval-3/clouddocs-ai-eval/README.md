# CloudDocs AI — Evaluation Harness

Automated accuracy test for the RAG pipeline. Uploads a known test document
(`sample_document.txt` — a fictional company policy handbook covering returns,
shipping, warranty, payments, and more), then asks 37 questions with known
expected answers and measures how many the system gets right — including
whether it correctly refuses to answer questions the document doesn't cover
(the hallucination check).

## Setup

```bash
pip install requests
```

## Run it

Against your deployed backend:
```bash
python run_eval.py --api-url https://clouddocs-ai.onrender.com
```

Against your local backend (must be running first):
```bash
python run_eval.py --api-url http://localhost:8000
```

## What it measures

- **Overall accuracy** — % of all 37 questions answered correctly
- **Answerable-question accuracy** — % correct among the 33 questions the
  document actually covers (tests retrieval + generation quality)
- **Correct-refusal rate** — % of the 4 out-of-scope questions (e.g. "who is
  the CEO?") where the system correctly said it doesn't know, instead of
  hallucinating an answer

## Output

- Console output showing PASS/FAIL per question as it runs
- `eval_report.md` — a full markdown report with every question, answer, and
  result, generated after each run — good for a screenshot or a GitHub commit
  showing the number over time

## Results

Latest run against the deployed backend (Render + Groq + Supabase):

| Metric | Score |
|---|---|
| Overall accuracy | 86.5% (32/37) |
| Answerable-question accuracy | 84.8% |
| Correct-refusal rate (out-of-scope questions) | 100% |

The system never hallucinated an answer to a question outside the document's
scope — every out-of-scope question was correctly identified as unanswerable.
The few misses on answerable questions were mostly chunk-boundary retrieval
gaps (a fact split across two chunks, with only one retrieved), addressed by
increasing chunk size, overlap, and retrieved-passage count.

## Scoring method

Each question has a list of `expected_keywords`. An answer is marked correct
if at least one expected keyword appears in it (case-insensitive). This is a
simple, transparent method appropriate for a portfolio project — a production
system would typically use a second LLM call as a judge, or human review, for
more nuanced scoring.
