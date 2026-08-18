# tests/eval_harness.py
"""
Golden QA evaluation harness for MedBot.

Runs each question in golden_qa.json through the real pipeline and checks
actual behavior against expected behavior. Reports per-question results
plus aggregate metrics: message-type accuracy, verdict accuracy, groundedness
accuracy, keyword coverage, and citation-page recall.

Usage:
    uv run python tests/eval_harness.py
    uv run python tests/eval_harness.py --verbose      # show full answers
    uv run python tests/eval_harness.py --filter cardio  # run only matching ids
"""
import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# allow running as `python tests/eval_harness.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.build import run_query


@dataclass
class QuestionResult:
    id: str
    question: str
    passed: bool
    checks: dict = field(default_factory=dict)
    keyword_coverage: Optional[float] = None
    page_recall: Optional[float] = None
    elapsed_s: float = 0.0
    actual_answer: str = ""
    notes: str = ""


def load_golden_set(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_keywords(answer: str, expected_keywords: List[str]) -> Optional[float]:
    if not expected_keywords:
        return None
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return hits / len(expected_keywords)


def check_page_recall(citations: List[dict], expected_pages: List[int]) -> Optional[float]:
    if not expected_pages:
        return None
    actual_pages = {c.get("page") for c in citations}
    hits = sum(1 for p in expected_pages if p in actual_pages)
    return hits / len(expected_pages)


def evaluate_question(item: dict, verbose: bool = False) -> QuestionResult:
    qid = item["id"]
    question = item["question"]

    start = time.time()
    try:
        result = run_query(question, bypass_cache=True)
    except Exception as e:
        return QuestionResult(
            id=qid, question=question, passed=False,
            checks={"error": f"Pipeline crashed: {e}"}, notes=item.get("notes", ""),
        )
    elapsed = time.time() - start

    checks = {}
    passed = True

    # message_type check
    if item.get("expected_type") is not None:
        actual_type = result.get("message_type")
        ok = actual_type == item["expected_type"]
        checks["message_type"] = f"{'PASS' if ok else 'FAIL'} (expected={item['expected_type']}, actual={actual_type})"
        passed &= ok

    # is_emergency check
    if item.get("expected_emergency") is not None:
        actual_emergency = result.get("is_emergency", False)
        ok = actual_emergency == item["expected_emergency"]
        checks["is_emergency"] = f"{'PASS' if ok else 'FAIL'} (expected={item['expected_emergency']}, actual={actual_emergency})"
        passed &= ok

    # verdict check
    if item.get("expected_verdict") is not None:
        actual_verdict = result.get("verdict")
        ok = actual_verdict == item["expected_verdict"]
        checks["verdict"] = f"{'PASS' if ok else 'FAIL'} (expected={item['expected_verdict']}, actual={actual_verdict})"
        passed &= ok

    # groundedness check
    if item.get("expected_grounded") is not None:
        g = result.get("groundedness")
        actual_grounded = g.grounded if g else None
        ok = actual_grounded == item["expected_grounded"]
        checks["grounded"] = f"{'PASS' if ok else 'FAIL'} (expected={item['expected_grounded']}, actual={actual_grounded})"
        passed &= ok

    answer = result.get("final_answer", "") or result.get("answer", "") or ""

    kw_coverage = check_keywords(answer, item.get("expected_keywords", []))
    if kw_coverage is not None:
        checks["keyword_coverage"] = f"{kw_coverage:.0%}"
        passed &= kw_coverage >= 0.5  # at least half the expected keywords should appear

    page_recall = check_page_recall(result.get("citations", []), item.get("expected_pages", []))
    if page_recall is not None:
        checks["page_recall"] = f"{page_recall:.0%}"
        passed &= page_recall >= 0.5

    return QuestionResult(
        id=qid, question=question, passed=passed, checks=checks,
        keyword_coverage=kw_coverage, page_recall=page_recall,
        elapsed_s=elapsed, actual_answer=answer if verbose else answer[:200],
        notes=item.get("notes", ""),
    )


def print_report(results: List[QuestionResult], verbose: bool):
    print("\n" + "=" * 70)
    print("MEDBOT EVAL REPORT")
    print("=" * 70)

    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        print(f"\n[{status}] {r.id}  ({r.elapsed_s:.1f}s)")
        print(f"  Q: {r.question}")
        for check_name, check_result in r.checks.items():
            print(f"  - {check_name}: {check_result}")
        if r.notes:
            print(f"  note: {r.notes}")
        if verbose:
            print(f"  answer: {r.actual_answer}")

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_time = sum(r.elapsed_s for r in results) / total if total else 0

    kw_scores = [r.keyword_coverage for r in results if r.keyword_coverage is not None]
    page_scores = [r.page_recall for r in results if r.page_recall is not None]

    print("\n" + "-" * 70)
    print(f"TOTAL: {passed}/{total} passed ({passed/total:.0%})")
    print(f"Avg response time: {avg_time:.2f}s")
    if kw_scores:
        print(f"Avg keyword coverage: {sum(kw_scores)/len(kw_scores):.0%}")
    if page_scores:
        print(f"Avg citation page recall: {sum(page_scores)/len(page_scores):.0%}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="tests/golden_qa.json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--filter", default=None, help="Only run questions whose id contains this substring")
    args = parser.parse_args()

    golden_set = load_golden_set(args.golden_set)
    if args.filter:
        golden_set = [q for q in golden_set if args.filter in q["id"]]

    print(f"Running {len(golden_set)} golden questions...")

    results = []
    for item in golden_set:
        print(f"  running: {item['id']}...")
        results.append(evaluate_question(item, verbose=args.verbose))

    print_report(results, verbose=args.verbose)

    failed = [r for r in results if not r.passed]
    if failed:
        sys.exit(1)  # non-zero exit for CI integration later


if __name__ == "__main__":
    main()
    
    