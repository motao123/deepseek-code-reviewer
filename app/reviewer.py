import asyncio
import json
import os
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from .context import ContextBuilder
from .prompts import SYSTEM_PROMPT
from .utils import robust_json_parse


@dataclass
class ReviewResult:
    file_path: str
    summary: dict = field(default_factory=dict)
    issues: list[dict] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    raw_tokens: int = 0


class DeepSeekReviewer:
    """基于 DeepSeek V4 的代码审查引擎"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com",
        repo_root: str = ".",
        max_context_tokens: int = 60000,
    ):
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.context_builder = ContextBuilder(
            repo_root=repo_root, max_context_tokens=max_context_tokens
        )

    async def review_pr(self, changed_files: list[str]) -> list[ReviewResult]:
        context = self.context_builder.build_context(changed_files)
        tasks = [self._review_single_file(f, context) for f in changed_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for f, result in zip(changed_files, results):
            if isinstance(result, Exception):
                final_results.append(ReviewResult(
                    file_path=f,
                    summary={"error": str(result)},
                ))
            else:
                final_results.append(result)

        return final_results

    async def _review_single_file(
        self, file_path: str, context: str
    ) -> ReviewResult:
        file_path_abs = os.path.join(self.context_builder.repo_root, file_path)
        try:
            with open(file_path_abs, "r", encoding="utf-8") as fh:
                file_content = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            return ReviewResult(
                file_path=file_path,
                summary={"error": str(e)},
            )

        user_prompt = f"""## 上下文信息

{context}

## 待审查文件：{file_path}

```python
{file_content}
```

请按照审查规则逐项审查以上代码，输出 JSON 格式的审查报告。
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content or "{}"
                review_data = robust_json_parse(content)
                tokens = response.usage.total_tokens if response.usage else 0

                return ReviewResult(
                    file_path=file_path,
                    summary=review_data.get("summary", {}),
                    issues=review_data.get("issues", []),
                    highlights=review_data.get("highlights", []),
                    raw_tokens=tokens,
                )

            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                raise
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        return ReviewResult(file_path=file_path, summary={"error": "max retries exceeded"})
