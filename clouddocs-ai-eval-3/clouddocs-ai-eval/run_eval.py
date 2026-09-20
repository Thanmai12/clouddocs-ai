"""
CloudDocs AI — Evaluation Harness

Uploads a known test document to the live (or local) API, runs a fixed set of
questions with known expected keywords, and measures how many answers are
correctly grounded — including whether the system correctly says "I don't know"
for questions the document doesn't cover.

Usage:
    python run_eval.py --api-url https://clouddocs-ai.onrender.com
    python run_eval.py --api-url http://localhost:8000   (for local testing)
"""

import argparse
import json
import time
import sys
from pathlib import Path

import requests

HERE = Path(__file__).parent
DOC_PATH = HERE / "sample_document.txt"
QUESTIONS_PATH = HERE / "eval_questions.json"
REPORT_PATH = HERE / "eval_report.md"


def upload_document(api_url: str) -> str:
    print("Uploading test document...")
    with open(DOC_PATH, "rb") as f:
        files = {"file": ("cloudcart_policy.txt", f, "text/plain")}
        resp = requests.post(f"{api_url}/documents", files=files, timeout=30)
    resp.raise_for_status()
    doc = resp.json()
    print(f"Uploaded. Document ID: {doc['id']}")
    return doc["id"]


def wait_until_ready(api_url: str, document_id: str, timeout_s: int = 120) -> None:
    print("Waiting for processing to complete", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(f"{api_url}/documents/{document_id}", timeout=15)
        resp.raise_for_status()
        status = resp.json()["status"]
        if status == "ready":
            print(" done.")
            return
        if status == "failed":
            raise RuntimeError(f"Document processing failed: {resp.json()}")
        print(".", end="", flush=True)
        time.sleep(2)
    raise TimeoutError("Document did not become ready in time.")


def ask(api_url: str, document_id: str, question: str) -> str:
    resp = requests.post(
        f"{api_url}/chat/query",
        json={"document_id": document_id, "question": question},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["answer"]


def score_answer(answer: str, expected_keywords: list[str], answerable: bool) -> bool:
    """
    Normalizes whitespace (collapses multiple/non-breaking spaces to single
    regular spaces) before matching, since LLM markdown formatting can insert
    inconsistent spacing around bolded terms.
    """
    import re
    answer_norm = re.sub(r"\s+", " ", answer.lower())
    matched = any(
        re.sub(r"\s+", " ", kw.lower()) in answer_norm
        for kw in expected_keywords
    )
    return matched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True, help="Base URL of the running API")
    args = parser.parse_args()
    api_url = args.api_url.rstrip("/")

    questions = json.loads(QUESTIONS_PATH.read_text())

    document_id = upload_document(api_url)
    wait_until_ready(api_url, document_id)

    results = []
    print(f"\nRunning {len(questions)} evaluation questions...\n")

    for q in questions:
        try:
            answer = ask(api_url, document_id, q["question"])
        except Exception as exc:  # noqa: BLE001
            answer = f"[ERROR: {exc}]"

        correct = score_answer(answer, q["expected_keywords"], q["answerable"])
        status = "PASS" if correct else "FAIL"
        print(f"[{status}] Q{q['id']}: {q['question']}")

        results.append({
            "id": q["id"],
            "question": q["question"],
            "answer": answer,
            "answerable": q["answerable"],
            "correct": correct,
        })

    total = len(results)
    passed = sum(1 for r in results if r["correct"])
    accuracy = passed / total * 100 if total else 0

    answerable_results = [r for r in results if r["answerable"]]
    unanswerable_results = [r for r in results if not r["answerable"]]
    answerable_acc = (
        sum(1 for r in answerable_results if r["correct"]) / len(answerable_results) * 100
        if answerable_results else 0
    )
    refusal_acc = (
        sum(1 for r in unanswerable_results if r["correct"]) / len(unanswerable_results) * 100
        if unanswerable_results else 0
    )

    print(f"\n{'='*50}")
    print(f"Overall accuracy: {passed}/{total} ({accuracy:.1f}%)")
    print(f"Answerable-question accuracy: {answerable_acc:.1f}%")
    print(f"Correct-refusal rate (out-of-scope questions): {refusal_acc:.1f}%")
    print(f"{'='*50}\n")

    write_report(results, accuracy, answerable_acc, refusal_acc, api_url)
    print(f"Full report written to {REPORT_PATH}")


def write_report(results, accuracy, answerable_acc, refusal_acc, api_url):
    lines = [
        "# CloudDocs AI — Evaluation Report",
        "",
        f"**API tested:** `{api_url}`",
        f"**Total questions:** {len(results)}",
        f"**Overall accuracy:** {accuracy:.1f}%",
        f"**Answerable-question accuracy:** {answerable_acc:.1f}%",
        f"**Correct-refusal rate (out-of-scope questions):** {refusal_acc:.1f}%",
        "",
        "## Per-question results",
        "",
        "| # | Result | Question | Answer (truncated) |",
        "|---|--------|----------|---------------------|",
    ]
    for r in results:
        status = "✅" if r["correct"] else "❌"
        answer_short = r["answer"].replace("\n", " ")[:100]
        lines.append(f"| {r['id']} | {status} | {r['question']} | {answer_short}... |")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as exc:
        print(f"\nRequest failed: {exc}")
        sys.exit(1)
