import logging
import os
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .reviewer import DeepSeekReviewer
from .batch import BatchReviewStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DeepSeek Code Reviewer",
    description="基于 DeepSeek V4 的智能代码审查 Agent",
    version="0.1.0",
)

reviewer = DeepSeekReviewer(
    repo_root=os.environ.get("REPO_ROOT", "."),
    max_context_tokens=int(os.environ.get("MAX_CONTEXT_TOKENS", "60000")),
)
batch_strategy = BatchReviewStrategy(
    repo_root=os.environ.get("REPO_ROOT", "."),
    batch_size=int(os.environ.get("BATCH_SIZE", "10")),
)


# ────────── Pydantic models ──────────

class ReviewRequest(BaseModel):
    files: List[str] = Field(..., description="待审查的文件路径列表")


class ReviewIssue(BaseModel):
    severity: str
    category: str
    file: str
    line: int
    title: str
    description: str
    suggestion: str


class ReviewSummary(BaseModel):
    total_issues: int
    high: int
    medium: int
    low: int
    overall_score: float | None = None


class ReviewResponse(BaseModel):
    summary: ReviewSummary
    issues: List[ReviewIssue]
    highlights: List[str]


# ────────── Routes ──────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
async def review_code(req: ReviewRequest):
    if not req.files:
        raise HTTPException(status_code=400, detail="files list cannot be empty")

    all_results = []
    batches = batch_strategy.split_batches(req.files)
    logger.info(f"Reviewing {len(req.files)} file(s) in {len(batches)} batch(es)")

    for batch in batches:
        batch_results = await reviewer.review_pr(batch)
        all_results.extend(batch_results)

    all_issues: list[dict] = []
    all_highlights: list[str] = []
    total_tokens = 0

    for result in all_results:
        for issue in result.issues:
            issue["file"] = result.file_path
            all_issues.append(issue)
        all_highlights.extend(result.highlights)
        total_tokens += result.raw_tokens

    high = sum(1 for i in all_issues if i.get("severity") == "high")
    medium = sum(1 for i in all_issues if i.get("severity") == "medium")
    low = sum(1 for i in all_issues if i.get("severity") == "low")

    logger.info(f"Review done: {len(all_issues)} issues, {total_tokens} tokens")

    return ReviewResponse(
        summary=ReviewSummary(
            total_issues=len(all_issues),
            high=high,
            medium=medium,
            low=low,
        ),
        issues=all_issues,
        highlights=all_highlights,
    )


@app.post("/review/async")
async def review_code_async(req: ReviewRequest):
    from .tasks import review_pr_task

    if not req.files:
        raise HTTPException(status_code=400, detail="files list cannot be empty")

    task = review_pr_task.delay(req.files)
    return JSONResponse({"task_id": task.id, "status": "queued"})


@app.get("/review/status/{task_id}")
async def review_status(task_id: str):
    from celery.result import AsyncResult
    from .tasks import celery_app

    result = AsyncResult(task_id, app=celery_app)
    resp = {"task_id": task_id, "status": result.state}
    if result.ready():
        resp["result"] = result.result
    elif result.failed():
        resp["error"] = str(result.info)
    return resp


# ────────── GitHub Webhook ──────────

@app.post("/webhook")
async def github_webhook(request: Request):
    """接收 GitHub PR Webhook 事件，自动触发审查"""
    from .github import (
        get_pr_changed_files,
        get_pr_diff,
        post_pr_comment,
        build_summary_comment,
    )
    from .tasks import review_pr_task

    event_type = request.headers.get("X-GitHub-Event", "ping")
    body = await request.json()

    if event_type == "ping":
        return {"status": "ok", "message": "Webhook configured successfully"}

    if event_type != "pull_request":
        return {"status": "ignored", "event": event_type}

    action = body.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    pr_number = body.get("number") or body["pull_request"]["number"]
    repo_full = body["repository"]["full_name"]

    logger.info(f"Webhook: PR #{pr_number} in {repo_full} ({action})")

    # 获取变更文件
    try:
        changed_files = get_pr_changed_files(repo_full, pr_number)
    except Exception as e:
        logger.error(f"Failed to fetch PR files: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

    if not changed_files:
        post_pr_comment(repo_full, pr_number, "  未检测到需要审查的代码文件变更。")
        return {"status": "ok", "files": 0}

    # 发一条 "审查中" 评论
    post_pr_comment(
        repo_full,
        pr_number,
        f"  DeepSeek V4 正在审查 **{len(changed_files)}** 个文件，请稍候...",
    )

    # 异步审查
    task = review_pr_task.delay(changed_files)

    return {"status": "queued", "task_id": task.id, "files": len(changed_files)}
