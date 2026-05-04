import json
import re


def robust_json_parse(raw: str) -> dict:
    """容错 JSON 解析，处理模型输出非标准 JSON 的情况"""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 尝试用正则提取第一个 JSON 对象
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 修复常见格式问题后重新解析
    fixed = raw.strip()
    fixed = re.sub(r",\s*\}", "}", fixed)     # 尾部多余逗号
    fixed = re.sub(r",\s*\]", "]", fixed)     # 数组尾部多余逗号
    return json.loads(fixed)


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数"""
    return len(text) // 3
