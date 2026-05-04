"""CLI 入口：命令行直接运行审查"""
import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app.reviewer import DeepSeekReviewer
from app.batch import BatchReviewStrategy


def print_result(result):
    """彩色打印审查结果"""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    issues = result.issues
    if not issues:
        print(f"{GREEN}{BOLD}  No issues found in {result.file_path}{RESET}")
        return

    print(f"\n{BOLD}  {result.file_path}{RESET} — {len(issues)} issue(s)")
    for issue in issues:
        sev_color = RED if issue.get("severity") == "high" else YELLOW
        print(f"  {sev_color}[{issue.get('severity', '?')}]{RESET} "
              f"[{issue.get('category', '?')}] {issue.get('title', '')}")
        print(f"      {CYAN}Line {issue.get('line', '?')}{RESET}: {issue.get('description', '')}")
        suggestion = issue.get("suggestion", "")
        if suggestion:
            print(f"      {GREEN}Fix:{RESET} {suggestion[:120]}")
    print()


async def main():
    parser = argparse.ArgumentParser(description="DeepSeek V4 Code Reviewer")
    parser.add_argument("files", nargs="+", help="Files to review")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--max-tokens", type=int, default=60000, help="Max context tokens")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for large PRs")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not set. Set it in .env or environment.", file=sys.stderr)
        sys.exit(1)

    reviewer = DeepSeekReviewer(
        api_key=api_key,
        repo_root=args.repo_root,
        max_context_tokens=args.max_tokens,
    )
    batcher = BatchReviewStrategy(repo_root=args.repo_root, batch_size=args.batch_size)

    batches = batcher.split_batches(args.files)
    print(f"Reviewing {len(args.files)} file(s) in {len(batches)} batch(es)...")

    all_results = []
    total_tokens = 0

    for i, batch in enumerate(batches, 1):
        print(f"\nBatch {i}/{len(batches)}: {', '.join(batch)}")
        results = await reviewer.review_pr(batch)
        all_results.extend(results)
        for r in results:
            total_tokens += r.raw_tokens
            print_result(r)

    # Summary
    all_issues = []
    for r in all_results:
        for issue in r.issues:
            issue["_file"] = r.file_path
            all_issues.append(issue)

    high = sum(1 for i in all_issues if i.get("severity") == "high")
    medium = sum(1 for i in all_issues if i.get("severity") == "medium")
    low = sum(1 for i in all_issues if i.get("severity") == "low")

    print(f"\n{'='*50}")
    print(f"Review complete: {len(all_issues)} issue(s) found")
    print(f"  High: {high}  Medium: {medium}  Low: {low}")
    print(f"  Total tokens used: {total_tokens}")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
