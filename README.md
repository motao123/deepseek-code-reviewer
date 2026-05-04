# DeepSeek Code Reviewer

基于 DeepSeek V4 API 的智能代码审查 Agent，支持本地部署和 GitHub 集成。

## 功能

- **多维度审查**：安全漏洞、逻辑错误、代码规范、性能问题、可维护性
- **上下文裁剪**：按依赖关系智能裁剪审查上下文，控制 Token 消耗
- **分批审查**：大 PR 自动拆批次，避免超时
- **同步/异步**：支持 REST API 即时审查，也支持 Celery 队列异步处理

## 快速开始

### 1. 安装

```bash
git clone <repo-url>
cd deepseek-code-reviewer
pip install -r requirements.txt
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 3. 命令行使用

```bash
python run.py app/context.py app/reviewer.py
```

### 4. API 服务

```bash
uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs
```

### 5. Docker 部署

```bash
docker compose up -d
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/review` | 同步审查，返回结果 |
| POST | `/review/async` | 异步审查，返回 task_id |
| GET | `/review/status/{task_id}` | 查询异步任务状态 |
