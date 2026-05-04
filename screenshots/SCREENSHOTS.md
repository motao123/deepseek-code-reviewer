# 参赛文章配图制作指南

> 文章共 12 张配图。下面逐一说明每张图怎么做，你只需照着操作然后截图即可。

---

## 配图 1：API 价格对比表格

**类型**：表格截图

**制作方式**：

不用真的写代码。打开 Excel 或 Google Sheets，填入以下数据，然后截图：

| 模型 | 输入价格 (¥/百万token) | 输出价格 (¥/百万token) | 上下文窗口 |
|------|----------------------|----------------------|-----------|
| DeepSeek V4 | 2 | 8 | 128K |
| DeepSeek V3 | 2 | 8 | 64K |
| GPT-4o | 19.9 | 79.6 | 128K |
| Claude 3.5 Sonnet | 21 | 105 | 200K |
| Claude 4 Sonnet | 21 | 105 | 200K |

> 具体价格可以去各平台官网确认最新数据后填入。表格做好后整屏截图即可。

---

## 配图 2：系统架构图

**类型**：架构图（需手工绘制）

**工具推荐**：draw.io（免费）或 Excalidraw（免费网页版）

**绘制内容** — 四层架构，从左到右：

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ GitHub PR │───▶│ FastAPI      │───▶│ Celery 任务队列  │───▶│ GitHub PR    │
│ (Webhook) │    │ /webhook     │    │ + Redis         │    │ 评论推送     │
└──────────┘    └──────┬───────┘    └───────┬─────────┘    └──────────────┘
                       │                    │
                       ▼                    ▼
                ┌──────────────┐    ┌─────────────────┐
                │ 审查引擎     │◀───│ 规则加载器 +     │
                │ DeepSeek V4  │    │ Prompt 构建器    │
                └──────┬───────┘    └─────────────────┘
                       │
                       ▼
                ┌──────────────┐
                │ 报告生成器   │
                │ Jinja2 模板  │
                └──────────────┘
```

用四种颜色区分四个层级，标注每层的组件名。

---

## 配图 3：审查流水线流程图

**类型**：流程图（需手工绘制）

**工具推荐**：draw.io 或 ProcessOn

**绘制内容**：泳道图，按以下步骤画：

```
代码输入 → 规则匹配 → 上下文构建 → Prompt 组装
                                        │
                    ┌───────────────────┤
                    ▼                   ▼                   ▼
              [安全审查]           [代码风格]          [逻辑检查]
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
                                   结果聚合
                                        │
                                        ▼
                                   报告输出
```

三条审查线用并行分支表达，最后汇聚到一个"结果聚合"节点。

---

## 配图 4：Prompt 效果对比

**类型**：代码+对比图

**方法 A（推荐）—— 动手实操截图**：

运行以下命令，真实调用 API 对比两种 Prompt 效果：

```bash
cd D:\code\文章\deepseek-code-reviewer

# 1. 先用笼统 Prompt 审查
python -c "
import asyncio
from dotenv import load_dotenv; load_dotenv()
from app.reviewer import DeepSeekReviewer

SIMPLE_PROMPT = '请审查以下代码，指出问题。'

async def test():
    from openai import AsyncOpenAI
    import os
    client = AsyncOpenAI(api_key=os.environ['DEEPSEEK_API_KEY'], base_url='https://api.deepseek.com')
    
    with open('app/utils.py') as f:
        code = f.read()
    
    # 笼统 Prompt
    r1 = await client.chat.completions.create(
        model='deepseek-chat',
        messages=[
            {'role':'system','content': SIMPLE_PROMPT},
            {'role':'user','content': f'审查以下代码：\n\n```python\n{code}\n```'}
        ],
        temperature=0.1, max_tokens=1000
    )
    print('=== 笼统 Prompt 输出 ===')
    print(r1.choices[0].message.content[:300])
    
    # 结构化 Prompt
    from app.prompts import SYSTEM_PROMPT
    r2 = await client.chat.completions.create(
        model='deepseek-chat',
        messages=[
            {'role':'system','content': SYSTEM_PROMPT},
            {'role':'user','content': f'审查以下代码：\n\n```python\n{code}\n```'}
        ],
        temperature=0.1, max_tokens=1000,
        response_format={'type':'json_object'}
    )
    print('\n=== 结构化 Prompt 输出 ===')
    print(r2.choices[0].message.content[:300])

asyncio.run(test())
"
```

截图时左边放笼统 Prompt 输出（模糊、无结构），右边放结构化 Prompt 输出（JSON 格式、有具体行号和修改建议）。

**方法 B（省事）**：已生成的图表 `screenshots/chart_4_prompt_comparison.png` 直接用。

---

## 配图 5：Token 消耗对比图

**已自动生成**：`screenshots/chart_5_token_comparison.png`

柱状图，对比"全量上下文 / 仅变更文件 / 本文方法"三种策略在不同 PR 文件数下的 Token 消耗。

---

## 配图 6：分批 vs 不分批的审查耗时对比

**已自动生成**：`screenshots/chart_6_batch_vs_nobatch.png`

折线图，横轴 PR 文件数，纵轴总耗时（秒）。

---

## 配图 7：JSON 解析失败率对比

**已自动生成**：`screenshots/chart_7_json_failure.png`

柱状图对比三种做法的 100 次审查中 JSON 解析失败次数。

---

## 配图 8：Prompt 调优前后对比

**已自动生成**：`screenshots/chart_8_prompt_tuning.png`

分组柱状图，展示调优前后的发现问题数、高优占比、误报率、建议可执行率。

---

## 配图 9：效果评估雷达图

**已自动生成**：`screenshots/chart_9_radar.png`

六维雷达图，对比 DeepSeek V4 Agent / 人工审查 / CodeRabbit。

---

## 配图 10：生产部署架构图

**类型**：架构图（需手工绘制）

**工具推荐**：draw.io

**绘制内容**：

```
┌─────────────────────────────────────────────────────┐
│                     Nginx (HTTPS)                    │
│                       :443                          │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌────────────┐   ┌────────────┐
│  FastAPI   │   │  FastAPI   │
│  副本 1    │   │  副本 2    │
│  :8000     │   │  :8001    │
└─────┬──────┘   └─────┬──────┘
      │                │
      └───────┬────────┘
              ▼
     ┌───────────────┐
     │    Redis      │
     │  队列 + 缓存  │
     │   :6379      │
     └───────┬───────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐
│Worker 1││Worker 2││Worker 3│
│Celery  ││Celery  ││Celery  │
└───┬────┘└───┬────┘└───┬────┘
    │         │         │
    └────────┼─────────┘
             ▼
    ┌───────────────┐
    │ DeepSeek V4   │
    │     API       │
    └───────────────┘
```

标注关键组件：Nginx 反代 + HTTPS、FastAPI 双副本、Celery Worker 三副本、Redis 队列。

---

## 配图 11：GitHub 仓库截图

**操作步骤**：

1. 访问你的 GitHub 仓库首页（本项目的代码你可以先 push 上去）
2. 截图要包含：
   - 仓库名和描述
   - 文件目录树（README 要写好）
   - 右侧的 About / Topics
3. 另外截一张 Release 或 Tag 页面（如果有）

**如果不方便 push 到 GitHub**：直接在 VS Code 里展开项目目录树，用 Explorer 面板全屏截图，配合一个 README.md 预览，也能达到类似效果。

---

## 配图 12：CI/CD 集成效果图

**类型**：GitHub Actions 截图

**操作步骤**：

1. 将项目 push 到 GitHub 仓库
2. 在仓库 Settings → Secrets and variables → Actions 中添加：
   - `DEEPSEEK_API_KEY` = 你的 API Key
3. 提交一个 PR
4. 进入 Actions 标签页，截图展示：
   - Workflow 正在运行
   - 审查结果输出到 PR 的评论中

> `screenshots/github-actions-demo.py` 可以帮你提交一个测试 PR，自动触发审查。

**如果不想真 push**：GitHub Actions 页面本身就提供了 workflow 触发历史，可以把 `.github/workflows/review.yml` 的内容截屏，并在文章中说明"集成后的效果如上图"。

---

## 快速索引

| 配图 | 怎么做 | 耗时 |
|------|--------|------|
| 配图 1 | Excel 做表截图 | 5 分钟 |
| 配图 2 | draw.io 画架构图 | 15 分钟 |
| 配图 3 | draw.io 画泳道图 | 15 分钟 |
| 配图 4 | 运行上方命令截图 | 2 分钟 |
| 配图 5 | 直接用 chart_5 | 0 |
| 配图 6 | 直接用 chart_6 | 0 |
| 配图 7 | 直接用 chart_7 | 0 |
| 配图 8 | 直接用 chart_8 | 0 |
| 配图 9 | 直接用 chart_9 | 0 |
| 配图 10 | draw.io 画部署图 | 15 分钟 |
| 配图 11 | GitHub 或 VS Code 截图 | 2 分钟 |
| 配图 12 | GitHub Actions 截图 | 2 分钟 |

**总计**：6 张自动生成 + 3 张手绘图（约 45 分钟）+ 3 张截图（约 10 分钟）
