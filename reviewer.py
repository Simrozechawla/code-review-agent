import os
import sys
import json
import argparse
import time

import ollama
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from analyzer import analyze_code, format_analysis_for_prompt

load_dotenv()
console = Console()

SYSTEM_PROMPT = """You are a senior Python engineer doing a code review.
You will receive the source code and a static analysis report.
Respond ONLY with valid JSON. No preamble. No markdown fences.

Return exactly this structure:
{
  "summary": "2-3 sentence overall assessment",
  "score": <integer 1-10>,
  "issues": [
    {
      "line": <integer or null>,
      "severity": "high" | "medium" | "low",
      "category": "bug" | "security" | "style" | "performance" | "maintainability",
      "title": "short title",
      "description": "why this is a problem",
      "fix": "concrete fix"
    }
  ],
  "positives": ["things done well"],
  "recommended_next_steps": ["top 3 improvements in priority order"]
}"""


def build_prompt(code: str, analysis_report: str) -> str:
    return f"""{analysis_report}

=== SOURCE CODE ===
{code}
=== END SOURCE CODE ===

Return your structured JSON review now. Remember: ONLY valid JSON, nothing else."""


def call_ollama(code: str, analysis_report: str) -> dict:
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    with console.status(
        f"[bold purple]Sending to Ollama ({model})...", spinner="dots"
    ):
        start = time.time()
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(code, analysis_report)}
            ],
            options={"temperature": 0}
        )
        elapsed = round(time.time() - start, 2)

    console.print(
        f"[green]✓[/green] Ollama responded in [bold]{elapsed}s[/bold]"
    )

    raw = response["message"]["content"].strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]

    # Find JSON object in response in case model adds text before/after
    start_idx = raw.find("{")
    end_idx = raw.rfind("}") + 1
    if start_idx != -1 and end_idx > start_idx:
        raw = raw[start_idx:end_idx]

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON parse failed: {e}[/red]")
        console.print("[dim]Raw response:[/dim]")
        console.print(raw)
        sys.exit(1)


def display_results(review: dict, filename: str):
    score = review.get("score", 0)
    color = "green" if score >= 7 else "yellow" if score >= 4 else "red"

    console.print()
    console.print(Panel(
        f"[bold]Code Review: {filename}[/bold]\n"
        f"Score: [{color}]{score}/10[/{color}]\n\n"
        f"{review.get('summary', '')}",
        title="[bold blue]LLM Code Review Agent — Powered by Ollama[/bold blue]",
        border_style="blue"
    ))

    issues = review.get("issues", [])
    if issues:
        table = Table(
            title=f"Issues Found ({len(issues)})",
            box=box.ROUNDED,
            show_lines=True
        )
        table.add_column("Line", width=6)
        table.add_column("Severity", width=10)
        table.add_column("Category", width=16)
        table.add_column("Issue", width=30)
        table.add_column("Fix", width=34)

        sev_color = {"high": "red", "medium": "yellow", "low": "green"}
        sev_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(
            key=lambda x: sev_order.get(x.get("severity", "low"), 3)
        )

        for issue in issues:
            sev = issue.get("severity", "low")
            c = sev_color.get(sev, "white")
            table.add_row(
                str(issue.get("line", "—")),
                f"[{c}]{sev.upper()}[/{c}]",
                issue.get("category", ""),
                f"[bold]{issue.get('title', '')}[/bold]\n"
                f"[dim]{issue.get('description', '')}[/dim]",
                issue.get("fix", "")
            )

        console.print()
        console.print(table)

    positives = review.get("positives", [])
    if positives:
        console.print()
        console.print(Panel(
            "\n".join(f"[green]✓[/green] {p}" for p in positives),
            title="[green]What's done well[/green]",
            border_style="green"
        ))

    steps = review.get("recommended_next_steps", [])
    if steps:
        console.print()
        console.print(Panel(
            "\n".join(
                f"[bold]{i+1}.[/bold] {s}"
                for i, s in enumerate(steps)
            ),
            title="[yellow]Recommended next steps[/yellow]",
            border_style="yellow"
        ))

    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="LLM-powered Python code reviewer using Ollama"
    )
    parser.add_argument("file", help="Python file to review")
    parser.add_argument(
        "--save",
        help="Save JSON output to this path",
        default=None
    )
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            code = f.read()
    except FileNotFoundError:
        console.print(f"[red]File not found: {args.file}[/red]")
        sys.exit(1)

    if not code.strip():
        console.print("[red]File is empty.[/red]")
        sys.exit(1)

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    console.print(
        f"\n[bold]Analysing:[/bold] {args.file} "
        f"([dim]{len(code.splitlines())} lines[/dim]) "
        f"using [bold purple]{model}[/bold purple]"
    )

    with console.status("[bold]Running static analysis...", spinner="dots"):
        analysis = analyze_code(code)
        report = format_analysis_for_prompt(analysis, code)

    console.print(
        f"[green]✓[/green] Static analysis complete — "
        f"{len(analysis.get('issues_detected', []))} pre-detected issues"
    )

    review = call_ollama(code, report)
    display_results(review, args.file)

    if args.save:
        with open(args.save, "w") as f:
            json.dump(review, f, indent=2)
        console.print(f"[dim]Review saved to {args.save}[/dim]")


if __name__ == "__main__":
    main()