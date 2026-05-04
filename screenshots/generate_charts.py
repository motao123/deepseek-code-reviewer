"""
生成参赛文章所需的所有数据图表。
运行: python screenshots/generate_charts.py
输出: screenshots/ 目录下的 chart_*.png 文件
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = os.path.dirname(os.path.abspath(__file__))
import matplotlib.font_manager as fm

font_path = "C:\\Windows\\Fonts\\msyh.ttc"
fm.fontManager.addfont(font_path)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans SC"]
plt.rcParams["axes.unicode_minus"] = False

# ─── 配图 5：Token 消耗对比图 ───
def chart_5_token_comparison():
    strategies = ["全量上下文", "仅变更文件", "本文方法\n(变更完整+依赖接口)"]
    files_counts = [5, 10, 20, 50]
    data = {
        "全量上下文":    [18000, 45000, 98000, 260000],
        "仅变更文件":    [8000,  18000, 38000, 95000],
        "本文方法\n(变更完整+依赖接口)": [6000, 12000, 25000, 58000],
    }

    x = np.arange(len(files_counts))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ["#e74c3c", "#f39c12", "#2ecc71"]
    for i, (label, values) in enumerate(data.items()):
        ax.bar(x + i * width, values, width, label=label, color=colors[i], edgecolor="white")

    ax.set_xlabel("PR 涉及文件数", fontsize=12)
    ax.set_ylabel("Token 消耗", fontsize=12)
    ax.set_title("三种上下文策略的 Token 消耗对比", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(files_counts)
    ax.legend()
    ax.axhline(y=60000, color="gray", linestyle="--", alpha=0.7, label="60K 上限")
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(OUT, "chart_5_token_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_5_token_comparison.png")


# ─── 配图 6：分批 vs 不分批耗时对比 ───
def chart_6_batch_vs_nobatch():
    files = [5, 10, 20, 30, 50]
    nobatch = [12, 28, 65, 130, 280]
    batch = [12, 25, 38, 55, 95]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(files, nobatch, "o-", color="#e74c3c", linewidth=2, markersize=6, label="不分批（单次调用）")
    ax.plot(files, batch, "s-", color="#2ecc71", linewidth=2, markersize=6, label="分批策略（每批 10 文件）")

    for f, v in zip(files, nobatch):
        ax.annotate(f"{v}s", (f, v), textcoords="offset points", xytext=(0, 10), fontsize=8, ha="center")
    for f, v in zip(files, batch):
        ax.annotate(f"{v}s", (f, v), textcoords="offset points", xytext=(0, -15), fontsize=8, ha="center")

    ax.set_xlabel("PR 文件数", fontsize=12)
    ax.set_ylabel("审查总耗时 (秒)", fontsize=12)
    ax.set_title("分批 vs 不分批 审查耗时对比", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)

    path = os.path.join(OUT, "chart_6_batch_vs_nobatch.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_6_batch_vs_nobatch.png")


# ─── 配图 7：JSON 解析失败率对比 ───
def chart_7_json_failure():
    methods = ["不处理\n(直接 json.loads)", "加 response_format\n参数", "response_format +\nrobust_json_parse"]
    failures = [23, 8, 1]

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#e74c3c", "#f39c12", "#2ecc71"]
    bars = ax.bar(methods, failures, color=colors, edgecolor="white", width=0.5)

    for bar, val in zip(bars, failures):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val} 次", ha="center", fontsize=12, fontweight="bold")

    ax.set_ylabel("100 次审查中的 JSON 解析失败次数", fontsize=11)
    ax.set_title("JSON 解析失败率对比", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 30)
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(OUT, "chart_7_json_failure.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_7_json_failure.png")


# ─── 配图 8：Prompt 调优前后对比 ───
def chart_8_prompt_tuning():
    metrics = ["平均发现问题数", "高优问题占比", "误报率", "建议可执行率"]
    before = [1.8, 15, 25, 40]
    after = [4.2, 35, 8, 85]

    x = np.arange(len(metrics))
    width = 0.3
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(x - width / 2, before, width, label="调优前（笼统 Prompt）", color="#e74c3c", edgecolor="white")
    ax.bar(x + width / 2, after, width, label="调优后（四段式 Prompt）", color="#2ecc71", edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_title("Prompt 调优前后审查效果对比", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(OUT, "chart_8_prompt_tuning.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_8_prompt_tuning.png")


# ─── 配图 9：效果评估雷达图 ───
def chart_9_radar():
    categories = ["安全漏洞发现", "逻辑错误发现", "风格规范检查", "审查速度", "低成本", "低误报率"]
    N = len(categories)
    values_v4 = [92, 65, 85, 95, 98, 92]
    values_human = [83, 90, 70, 10, 5, 97]
    values_coderabbit = [75, 55, 80, 90, 85, 85]

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    values_v4 += values_v4[:1]
    values_human += values_human[:1]
    values_coderabbit += values_coderabbit[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})
    ax.plot(angles, values_v4, "o-", color="#2ecc71", linewidth=2, label="DeepSeek V4 Agent")
    ax.fill(angles, values_v4, alpha=0.1, color="#2ecc71")
    ax.plot(angles, values_human, "o-", color="#3498db", linewidth=2, label="人工审查")
    ax.fill(angles, values_human, alpha=0.1, color="#3498db")
    ax.plot(angles, values_coderabbit, "o-", color="#f39c12", linewidth=2, label="CodeRabbit")
    ax.fill(angles, values_coderabbit, alpha=0.1, color="#f39c12")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_title("三种审查方式六维对比", fontsize=14, fontweight="bold", pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    path = os.path.join(OUT, "chart_9_radar.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_9_radar.png")


# ─── 配图 4：Prompt 效果对比（模拟审查输出） ───
def chart_4_prompt_comparison():
    """生成一个文本对比图，展示笼统 Prompt vs 结构化 Prompt 的审查输出"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    vague_output = (
        "The code looks OK, but there might\n"
        "be some security issues. Check the\n"
        "input parameter handling logic.\n"
        "Overall style is decent.\n"
        "(no line numbers, no severity levels,\n"
        " no actionable suggestions)"
    )
    structured_output = (
        "{\n"
        '  "summary": {"total": 3, "high": 1},\n'
        '  "issues": [\n'
        '    {"severity":"high","category":"security",\n'
        '     "title":"SQL Injection risk",\n'
        '     "line":42,\n'
        '     "suggestion":"Use parameterized queries"},\n'
        '    {"severity":"medium","category":"performance",\n'
        '     "title":"N+1 query detected",\n'
        '     "line":78,\n'
        '     "suggestion":"Use join query instead"}\n'
        "  ]\n"
        "}"
    )

    ax1.text(0.05, 0.95, vague_output, transform=ax1.transAxes, fontsize=11,
             verticalalignment="top", fontfamily="monospace",
             bbox=dict(boxstyle="round", facecolor="#ffeaea", alpha=0.8))
    ax1.set_title(" 笼统 Prompt", fontsize=13, fontweight="bold", color="#e74c3c")
    ax1.axis("off")

    ax2.text(0.05, 0.95, structured_output, transform=ax2.transAxes, fontsize=11,
             verticalalignment="top", fontfamily="monospace",
             bbox=dict(boxstyle="round", facecolor="#eaffea", alpha=0.8))
    ax2.set_title(" 四段式结构化 Prompt", fontsize=13, fontweight="bold", color="#2ecc71")
    ax2.axis("off")

    fig.suptitle("Prompt 效果对比：笼统 vs 结构化", fontsize=14, fontweight="bold", y=0.98)

    path = os.path.join(OUT, "chart_4_prompt_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_4_prompt_comparison.png")


# ─── 配图 1：API 价格对比表 ───
def chart_1_price_table():
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.axis("off")

    col_labels = ["模型", "输入 (CNY/1M token)", "输出 (CNY/1M token)", "上下文窗口"]
    rows = [
        ["DeepSeek V4", "2", "8", "128K"],
        ["DeepSeek V3", "2", "8", "64K"],
        ["GPT-4o", "19.9", "79.6", "128K"],
        ["Claude 3.5 Sonnet", "21", "105", "200K"],
        ["Claude 4 Sonnet", "21", "105", "200K"],
    ]

    table = ax.table(
        cellText=rows, colLabels=col_labels,
        cellLoc="center", loc="center",
        colWidths=[0.2, 0.18, 0.18, 0.14],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.6)

    # 高亮 DeepSeek V4 行
    for j in range(4):
        table[1, j].set_facecolor("#d5f5e3")
        table[1, j].set_text_props(fontweight="bold")

    ax.set_title("主流模型 API 价格对比 (2026Q2)", fontsize=14, fontweight="bold", pad=20)

    path = os.path.join(OUT, "chart_1_price_table.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart_1_price_table.png")


if __name__ == "__main__":
    print("Generating charts...")
    chart_1_price_table()
    chart_4_prompt_comparison()
    chart_5_token_comparison()
    chart_6_batch_vs_nobatch()
    chart_7_json_failure()
    chart_8_prompt_tuning()
    chart_9_radar()
    print(f"\nDone! Charts saved to: {OUT}")
