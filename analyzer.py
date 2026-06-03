import ast


def analyze_code(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    results = {
        "functions": [],
        "classes": [],
        "imports": [],
        "issues_detected": []
    }

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):
            has_doc = (
                isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                if node.body else False
            )
            results["functions"].append({
                "name": node.name,
                "args": [a.arg for a in node.args.args],
                "has_docstring": has_doc,
                "line": node.lineno,
                "length": node.end_lineno - node.lineno + 1
            })
            if not has_doc:
                results["issues_detected"].append(
                    f"Function '{node.name}' at line {node.lineno} has no docstring"
                )

        elif isinstance(node, ast.ClassDef):
            results["classes"].append({
                "name": node.name,
                "line": node.lineno
            })
            if not node.name[0].isupper():
                results["issues_detected"].append(
                    f"Class '{node.name}' at line {node.lineno} violates PascalCase"
                )

        elif isinstance(node, ast.Import):
            for alias in node.names:
                results["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                results["imports"].append(node.module)

    code_body = "\n".join(
        l for l in code.split("\n")
        if not l.strip().startswith(("import", "from"))
    )
    for imp in results["imports"]:
        if imp and imp not in code_body:
            results["issues_detected"].append(
                f"Import '{imp}' appears unused"
            )

    return results


def format_analysis_for_prompt(analysis: dict, code: str) -> str:
    if "error" in analysis:
        return f"Static analysis failed: {analysis['error']}"

    lines = ["=== STATIC ANALYSIS ===\n"]
    lines.append(f"Total lines: {len(code.splitlines())}")
    lines.append(f"Functions: {len(analysis['functions'])}")
    lines.append(f"Classes: {len(analysis['classes'])}")
    lines.append(f"Imports: {', '.join(analysis['imports']) or 'none'}\n")

    if analysis["functions"]:
        lines.append("Function details:")
        for fn in analysis["functions"]:
            doc = "has docstring" if fn["has_docstring"] else "NO docstring"
            lines.append(
                f"  - {fn['name']}({', '.join(fn['args'])}) "
                f"line {fn['line']}, {fn['length']} lines, {doc}"
            )

    if analysis["issues_detected"]:
        lines.append("\nPre-detected issues:")
        for issue in analysis["issues_detected"]:
            lines.append(f"  ! {issue}")

    lines.append("\n=== END ANALYSIS ===")
    return "\n".join(lines)