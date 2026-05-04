"""GitHub 集成：获取 PR 文件、发布审查评论"""
import os
import httpx
from typing import Any


GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_pr_changed_files(repo_full: str, pr_number: int) -> list[str]:
    """获取 PR 变更文件列表"""
    url = f"{GITHUB_API}/repos/{repo_full}/pulls/{pr_number}/files"
    resp = httpx.get(url, headers=_headers(), params={"per_page": 100})
    resp.raise_for_status()
    files = resp.json()
    return [
        f["filename"]
        for f in files
        if not f["filename"].endswith((".lock", ".png", ".jpg", ".svg", ".ico"))
    ]


def get_pr_diff(repo_full: str, pr_number: int) -> str:
    """获取 PR 的完整 diff"""
    url = f"{GITHUB_API}/repos/{repo_full}/pulls/{pr_number}"
    headers = {**_headers(), "Accept": "application/vnd.github.v3.diff"}
    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def post_pr_comment(repo_full: str, pr_number: int, body: str) -> dict:
    """在 PR 下发布评论"""
    url = f"{GITHUB_API}/repos/{repo_full}/issues/{pr_number}/comments"
    resp = httpx.post(url, headers=_headers(), json={"body": body})
    resp.raise_for_status()
    return resp.json()


def post_inline_review(
    repo_full: str,
    pr_number: int,
    commit_id: str,
    comments: list[dict],
    body: str = "",
) -> dict:
    """以行级 Review 形式提交审查意见"""
    url = f"{GITHUB_API}/repos/{repo_full}/pulls/{pr_number}/reviews"
    payload: dict[str, Any] = {
        "commit_id": commit_id,
        "event": "COMMENT",
        "body": body or "DeepSeek V4 自动审查结果",
        "comments": [
            {
                "path": c["file"],
                "position": c["line"],
                "body": _format_review_comment(c),
            }
            for c in comments
            if c.get("line", 0) > 0
        ],
    }
    resp = httpx.post(url, headers=_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()


def _format_review_comment(issue: dict) -> str:
    sev_emoji = {"high": " 高危", "medium": " 中", "low": " 低"}
    sev = sev_emoji.get(issue.get("severity", ""), "")
    return f"""**{sev} [{issue.get('category', '')}] {issue.get('title', '')}**

{issue.get('description', '')}

建议修改：
```
{issue.get('suggestion', '')}
```"""


def build_summary_comment(results: list[dict], total_tokens: int) -> str:
    """生成 PR 总结评论"""
    all_issues = []
    for r in results:
        for issue in r.get("issues", []):
            issue["_file"] = r.get("file_path", "")
            all_issues.append(issue)

    high = sum(1 for i in all_issues if i.get("severity") == "high")
    medium = sum(1 for i in all_issues if i.get("severity") == "medium")
    low = sum(1 for i in all_issues if i.get("severity") == "low")

    lines = [
        "##   DeepSeek V4 代码审查报告",
        "",
        f"| 严重度 | 数量 |",
        f"|--------|------|",
        f"|   高危 | {high} |",
        f"|   中   | {medium} |",
        f"|   低   | {low} |",
        f"| **合计** | **{len(all_issues)}** |",
        "",
    ]

    if high > 0:
        lines.append("###   阻塞性问题（建议修改后再合并）")
        for i in all_issues:
            if i.get("severity") == "high":
                lines.append(
                    f"- **`{i.get('_file', '')}`** L{i.get('line', '?')}: "
                    f"{i.get('title', '')}"
                )
        lines.append("")

    if all_issues:
        lines.append("### 全部问题")
        for i in all_issues:
            lines.append(
                f"- [{i.get('severity', '?')}] **`{i.get('_file', '')}`** L{i.get('line', '?')}: "
                f"{i.get('title', '')}"
            )
    else:
        lines.append(" 未发现问题，代码质量良好！")

    lines.append("")
    lines.append(f"*审查消耗 {total_tokens} token · 由 DeepSeek V4 驱动*")

    return "\n".join(lines)
