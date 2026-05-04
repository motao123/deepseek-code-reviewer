import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("deepseek_reviewer", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True
celery_app.conf.task_time_limit = 600  # 单任务超时 10 分钟


@celery_app.task(name="app.tasks.review_pr")
def review_pr_task(pr_files: list[str]) -> dict:
    """Celery 异步任务：审查 PR"""
    import asyncio
    from .reviewer import DeepSeekReviewer

    reviewer = DeepSeekReviewer(repo_root=os.environ.get("REPO_ROOT", "."))
    results = asyncio.run(reviewer.review_pr(pr_files))

    issues = []
    total_tokens = 0
    for r in results:
        for issue in r.issues:
            issue["_file"] = r.file_path
            issues.append(issue)
        total_tokens += r.raw_tokens

    high = sum(1 for i in issues if i.get("severity") == "high")
    medium = sum(1 for i in issues if i.get("severity") == "medium")
    low = sum(1 for i in issues if i.get("severity") == "low")

    return {
        "issues": issues,
        "summary": {
            "total_issues": len(issues),
            "high": high,
            "medium": medium,
            "low": low,
            "total_tokens": total_tokens,
        },
    }
