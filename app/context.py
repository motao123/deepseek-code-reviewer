import ast
import os
from typing import Set, List


class ContextBuilder:
    """基于 AST 的代码上下文构建器，为审查提供最小且完整的上下文"""

    def __init__(self, repo_root: str = ".", max_context_tokens: int = 60000):
        self.repo_root = os.path.abspath(repo_root)
        self.max_tokens = max_context_tokens

    def build_context(self, changed_files: List[str]) -> str:
        imports_map: dict[str, set[str]] = {}
        context_files: Set[str] = set()

        for file_path in changed_files:
            imports = self._extract_local_imports(file_path)
            imports_map[file_path] = imports
            context_files.update(imports)

        context_parts = []

        # 变更文件 —— 完整内容
        for f in changed_files:
            content = self._read_file(f)
            if content is not None:
                context_parts.append(
                    f"// ===== {f} (CHANGED) =====\n{content}"
                )

        # 直接依赖 —— 只取公开接口
        for f in sorted(context_files):
            if f not in changed_files:
                interface = self._extract_public_interface(f)
                context_parts.append(
                    f"// ===== {f} (IMPORTED) =====\n{interface}"
                )

        full_context = "\n\n".join(context_parts)
        if self._estimate_tokens(full_context) > self.max_tokens:
            full_context = self._trim_context(context_parts)

        return full_context

    def _extract_local_imports(self, file_path: str) -> Set[str]:
        imports = set()
        full_path = os.path.join(self.repo_root, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        resolved = self._resolve_module_path(alias.name)
                        if resolved:
                            imports.add(resolved)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        resolved = self._resolve_module_path(node.module)
                        if resolved:
                            imports.add(resolved)
        except Exception:
            pass
        return imports

    def _resolve_module_path(self, module: str) -> str | None:
        parts = module.split(".")
        candidates = [
            os.path.join(*parts) + ".py",
            os.path.join(*parts, "__init__.py"),
        ]
        for c in candidates:
            if os.path.exists(os.path.join(self.repo_root, c)):
                return c
        return None

    def _extract_public_interface(self, file_path: str) -> str:
        full_path = os.path.join(self.repo_root, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as fh:
                source = fh.read()
            tree = ast.parse(source)
            lines = source.split("\n")
            interface_lines = []

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        line_num = node.lineno
                        body_0 = node.body[0]
                        is_str_expr = (
                            isinstance(body_0, ast.Expr)
                            and isinstance(body_0.value, ast.Constant)
                            and isinstance(body_0.value.value, str)
                        )
                        sig_end = body_0.lineno + 1 if is_str_expr else line_num + 1
                        interface_lines.extend(lines[line_num - 1 : sig_end])
                        interface_lines.append("    ...\n")
                elif isinstance(node, ast.ClassDef):
                    line_num = node.lineno
                    interface_lines.append(lines[line_num - 1])
                    interface_lines.append("    ...\n")
                elif isinstance(node, ast.Assign):
                    # 模块级常量
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            interface_lines.append(
                                lines[node.lineno - 1]
                            )
        except Exception:
            return f"# Failed to parse {file_path}"
        return "\n".join(interface_lines)

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 3

    def _trim_context(self, parts: List[str]) -> str:
        result = []
        token_budget = self.max_tokens
        for part in parts:
            part_tokens = self._estimate_tokens(part)
            if part_tokens <= token_budget:
                result.append(part)
                token_budget -= part_tokens
            else:
                chars = token_budget * 3
                result.append(part[:chars] + "\n// ... (truncated)")
                break
        return "\n\n".join(result)

    def _read_file(self, path: str) -> str | None:
        full_path = os.path.join(self.repo_root, path)
        try:
            with open(full_path, "r", encoding="utf-8") as fh:
                return fh.read()
        except (OSError, UnicodeDecodeError):
            return None
