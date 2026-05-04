# DeepSeek Code Reviewer 使用教程

本教程带你从零开始，完成部署、配置、使用的全流程。

---

## 目录

- [第一步：准备工作](#第一步准备工作)
- [第二步：获取 DeepSeek API Key](#第二步获取-deepseek-api-key)
- [第三步：安装项目](#第三步安装项目)
- [第四步：配置环境变量](#第四步配置环境变量)
- [第五步：命令行审查代码](#第五步命令行审查代码)
- [第六步：启动 API 服务](#第六步启动-api-服务)
- [第七步：Docker 部署（生产环境）](#第七步docker-部署生产环境)
- [第八步：接入 GitHub](#第八步接入-github)
- [附录：常见问题](#附录常见问题)

---

## 第一步：准备工作

### 环境要求

| 工具 | 最低版本 | 检查方式 |
|------|---------|----------|
| Python | 3.10+ | `python --version` |
| pip | 23.0+ | `pip --version` |
| Docker（可选） | 24.0+ | `docker --version` |

### 确认 Python 已安装

```bash
python --version
# 应输出类似：Python 3.12.0
```

如果未安装，去 [python.org](https://www.python.org/downloads/) 下载安装。**安装时务必勾选 "Add Python to PATH"**。


---

## 第二步：获取 DeepSeek API Key

### 2.1 注册并登录

打开 [platform.deepseek.com](https://platform.deepseek.com)，使用手机号或邮箱注册账号。


### 2.2 进入 API Keys 管理页

登录后，点击左侧菜单 **「API Keys」**。


### 2.3 创建 Key

点击 **「创建 API Key」** 按钮，输入名称（比如 `code-reviewer`），点击确认。


### 2.4 复制并保存 Key

**立即复制生成的 Key 并保存到安全的地方。** 关闭弹窗后将无法再次查看。

生成的 Key 格式类似：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`


### 2.5 充值（如需）

DeepSeek 新账号通常有赠送额度。如果额度用完，需要在 **「充值」** 页面充值。V4 模型价格约 **¥1/百万 token**，单个 PR 审查成本通常不超过 ¥0.1。


---

## 第三步：安装项目

### 3.1 进入项目目录

```bash
cd D:\code\文章\deepseek-code-reviewer
```


### 3.2 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

激活成功后，终端提示符前会出现 `(.venv)` 标识。


### 3.3 安装依赖

```bash
pip install -r requirements.txt
```

等待安装完成，应看到类似输出：

```
Successfully installed openai-... fastapi-... uvicorn-... ...
```


### 3.4 验证安装

```bash
python -c "from app.reviewer import DeepSeekReviewer; print('安装成功')"
```

如果输出 `安装成功`，说明一切就绪。

---

## 第四步：配置环境变量

### 4.1 复制配置模板

```bash
copy .env.example .env
```

### 4.2 编辑 .env 文件

用记事本或 VS Code 打开 `.env` 文件：

```bash
notepad .env
```

内容如下，替换 `sk-xxx` 为你的真实 Key：

```ini
DEEPSEEK_API_KEY=sk-你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
GITHUB_TOKEN=
REDIS_URL=redis://localhost:6379/0
MAX_CONTEXT_TOKENS=60000
BATCH_SIZE=10
```


### 4.3 各字段说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | **是** | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | 否 | API 地址，默认 https://api.deepseek.com |
| `GITHUB_TOKEN` | 否 | 推送到 PR 时需要，仅 GitHub 集成场景填写 |
| `REDIS_URL` | 否 | Celery 异步队列，仅生产模式需要 |
| `MAX_CONTEXT_TOKENS` | 否 | 单次审查上下文上限，默认 60000 |
| `BATCH_SIZE` | 否 | 大 PR 每批审查文件数，默认 10 |

---

## 第五步：命令行审查代码

### 5.1 基本用法

```bash
python run.py <文件1> <文件2> ...
```

### 5.2 审查单个文件

```bash
python run.py app/utils.py
```


你会看到类似输出：

```
Reviewing 1 file(s) in 1 batch(es)...

Batch 1/1: app/utils.py

  app/utils.py — 2 issue(s)
  [medium] [logic] 潜在的 JSON 解析异常传播
      Line 8: robust_json_parse 函数在异常情况下可能返回非预期结构
      Fix: 在调用 robust_json_parse 后增加返回值类型检查

  [low] [maintainability] 函数缺少文档说明
      Line 5: 公开函数 robust_json_parse 缺少 docstring
      Fix: 添加函数用途和参数的文档字符串

==================================================
Review complete: 2 issue(s) found
  High: 0  Medium: 1  Low: 1
  Total tokens used: 1449
==================================================
```

### 5.3 审查多个文件

```bash
python run.py app/utils.py app/context.py app/reviewer.py
```

### 5.4 审查整个模块

```bash
python run.py app/*.py
```

### 5.5 自定义参数

```bash
# 增大上下文窗口
python run.py --max-tokens 100000 app/large_file.py

# 指定仓库根目录
python run.py --repo-root ../my-project src/main.py

# 调整批次大小
python run.py --batch-size 5 app/*.py
```

### 5.6 命令行参数一览

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `files` | （必填） | 待审查的文件路径，支持多个 |
| `--repo-root` | `.` | 项目根目录，用于解析 import 依赖 |
| `--max-tokens` | `60000` | 上下文 token 上限 |
| `--batch-size` | `10` | 每批审查文件数 |

---

## 第六步：启动 API 服务

### 6.1 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```


`--reload` 参数表示代码修改后自动重启，开发时非常方便。

### 6.2 打开 Swagger 文档

浏览器打开 [http://localhost:8000/docs](http://localhost:8000/docs)


### 6.3 调用审查接口

在 Swagger 中：
1. 点击 `POST /review`
2. 点击 **「Try it out」**
3. 在 Request body 中填入：

```json
{
  "files": ["app/utils.py"]
}
```

4. 点击 **「Execute」**


### 6.4 返回结果示例

```json
{
  "summary": {
    "total_issues": 2,
    "high": 0,
    "medium": 1,
    "low": 1,
    "overall_score": null
  },
  "issues": [
    {
      "severity": "medium",
      "category": "logic",
      "file": "app/utils.py",
      "line": 8,
      "title": "潜在的 JSON 解析异常传播",
      "description": "robust_json_parse 在某些极端输入下可能抛出未捕获的异常",
      "suggestion": "添加 try-except 包裹 final json.loads 调用"
    }
  ],
  "highlights": ["三级容错设计增强了鲁棒性"]
}
```

### 6.5 用 curl 调用（无需浏览器）

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"files": ["app/utils.py"]}'
```

### 6.6 异步审查接口

```bash
# 提交异步任务
curl -X POST http://localhost:8000/review/async \
  -H "Content-Type: application/json" \
  -d '{"files": ["app/utils.py"]}'

# 返回：{"task_id":"abc123","status":"queued"}

# 查询任务状态
curl http://localhost:8000/review/status/abc123
```

> **注意**：异步接口需要 Redis 和 Celery Worker 运行，详见第七步。

---

## 第七步：Docker 部署（生产环境）

### 7.1 配置 .env

确保 `.env` 文件已正确填写 `DEEPSEEK_API_KEY`。

### 7.2 一键启动

```bash
docker compose up -d
```


这会启动三个服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| `api` | 8000 | FastAPI 服务 |
| `worker` | — | Celery 异步 Worker（3 并发） |
| `redis` | 6379 | 消息队列 + 结果缓存 |

### 7.3 验证运行状态

```bash
docker compose ps
# 三个服务状态应均为 Up

curl http://localhost:8000/health
# 返回 {"status":"ok"}
```


### 7.4 查看日志

```bash
# API 服务日志
docker compose logs api -f

# Worker 日志（查看审查任务执行）
docker compose logs worker -f
```

### 7.5 停止服务

```bash
docker compose down
```

---

## 第八步：接入 GitHub

### 8.1 整体流程

```
开发者提交 PR → GitHub Webhook 触发 → API 收到事件
→ Celery 队列异步审查 → 审查结果以评论形式回帖到 PR
```


### 8.2 创建 GitHub Token

1. 打开 [github.com/settings/tokens](https://github.com/settings/tokens)
2. 点击 **「Generate new token (classic)」**
3. 勾选权限：
   - `repo`（访问仓库）
   - `read:org`（如仓库在组织下）
4. 点击生成，复制 Token


### 8.3 配置 .env

```ini
GITHUB_TOKEN=ghp_你的GitHub Token
```

### 8.4 配置 GitHub Webhook

在目标仓库中：

1. 进入 **Settings** → **Webhooks** → **Add webhook**
2. Payload URL：`http://你的服务器地址:8000/webhook`
3. Content type：`application/json`
4. 勾选 **「Pull requests」** 事件
5. 点击 **Add webhook**


### 8.5 Webhook 路由（需自行扩展）

当前 `main.py` 未包含完整的 Webhook 处理路由，你可以参考以下代码扩展：

```python
@app.post("/webhook")
async def github_webhook(event: dict, request: Request):
    """接收 GitHub PR Webhook"""
    event_type = request.headers.get("X-GitHub-Event", "")

    if event_type == "pull_request":
        action = event.get("action", "")
        if action in ["opened", "synchronize"]:
            pr_number = event["number"]
            repo_full = event["repository"]["full_name"]

            # 获取 PR 变更文件列表
            changed_files = get_pr_changed_files(repo_full, pr_number)

            # 提交异步审查
            from .tasks import review_pr_task
            task = review_pr_task.delay(changed_files)

            # 在 PR 下留评论：审查进行中
            post_pr_comment(repo_full, pr_number,
                f"  DeepSeek V4 正在审查中...（任务 ID: {task.id}）")

    return {"status": "received"}
```


---

## 附录：常见问题

### Q1：提示 `ModuleNotFoundError`

```bash
# 先激活虚拟环境
.venv\Scripts\activate
# 再重装依赖
pip install -r requirements.txt
```

### Q2：提示 `DEEPSEEK_API_KEY not set`

检查 `.env` 文件是否存在且内容正确：

```bash
type .env
```

确保 `DEEPSEEK_API_KEY=sk-...` 行没有被 `#` 注释掉。

### Q3：返回 `401 Unauthorized`

- Key 是否正确复制（是否多了空格或换行）
- Key 是否已在 DeepSeek 后台被删除
- Key 余额是否已用完

### Q4：审查返回乱码

Windows 终端默认编码是 GBK。解决方案：

```bash
# 方案一：切换终端编码
chcp 65001

# 方案二：用 PowerShell 7+ 或 Windows Terminal

# 方案三：输出重定向到文件
python run.py app/utils.py > result.txt
notepad result.txt
```

### Q5：审查 2000 行的大文件超时

- 调大 `--max-tokens` 参数
- 文件会被 ContextBuilder 自动裁剪，如果仍然超时，考虑手动拆分文件

### Q6：异步审查任务一直 pending

确认 Redis 和 Celery Worker 已启动：

```bash
# 检查 Redis
docker compose ps redis

# 启动 Worker（本地模式）
celery -A app.tasks.celery_app worker --loglevel=info
```

---

> **下一步**：阅读 `README.md` 了解 API 接口详情，或直接修改 `app/prompts.py` 自定义你的审查规则。
