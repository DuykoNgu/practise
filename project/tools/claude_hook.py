from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "project" / "tools" / "check_screens.py"
SYNC_PATTERNS = (
    re.compile(r"^project/screens/[^/]+\.yaml$"),
    re.compile(r"^project/risks-and-questions\.md$"),
    re.compile(r"^docs/.+"),
    re.compile(r"^src/database/cic\.sql$"),
)
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}
SLASH_COMMENT = re.compile(r"(^|[^:\"'`\\])//|/\*")


def relative(path: str) -> str | None:
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def run_checker(write: bool) -> tuple[bool, str]:
    command = [sys.executable, str(CHECKER), *(["--write"] if write else [])]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def python_comments(source: str) -> list[int]:
    lines: list[int] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT and not (token.start[0] == 1 and token.string.startswith("#!")):
                lines.append(token.start[0])
    except (tokenize.TokenError, SyntaxError):
        return lines
    return lines


def script_comments(source: str) -> list[int]:
    lines: list[int] = []
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        starts_comment = stripped.startswith(("//", "/*", "*/")) or (stripped.startswith("*") and not stripped.startswith("**"))
        if starts_comment or SLASH_COMMENT.search(re.sub(r"(\"[^\"]*\"|'[^']*'|`[^`]*`)", "", line)):
            lines.append(number)
    return lines


def comment_lines(path: Path) -> list[int]:
    source = path.read_text(encoding="utf-8")
    return python_comments(source) if path.suffix == ".py" else script_comments(source)


def post_edit(payload: dict[str, object]) -> int:
    tool_input = payload.get("tool_input") or {}
    file_path = str(tool_input.get("file_path", "")) if isinstance(tool_input, dict) else ""
    rel = relative(file_path) if file_path else None
    if rel is None:
        return 0
    problems: list[str] = []
    if any(pattern.match(rel) for pattern in SYNC_PATTERNS):
        ok, output = run_checker(write=rel.startswith("project/screens/"))
        if not ok:
            problems.append(f"check_screens.py failed after editing {rel}:\n{output}")
    path = ROOT / rel
    if rel.startswith("src/") and path.suffix in CODE_SUFFIXES and path.exists():
        lines = comment_lines(path)
        if lines:
            shown = ", ".join(str(line) for line in lines[:20])
            problems.append(f"{rel} contains code comments on lines {shown}. CLAUDE.md §6 forbids comments; remove them.")
    if problems:
        print("\n\n".join(problems), file=sys.stderr)
        return 2
    return 0


def pre_commit() -> int:
    ok, output = run_checker(write=False)
    if ok:
        return 0
    print(f"Commit blocked: project/tools/check_screens.py reports problems.\n{output}", file=sys.stderr)
    return 2


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = json.loads(sys.stdin.read() or "{}")
    if mode == "post-edit":
        return post_edit(payload)
    if mode == "pre-commit":
        return pre_commit()
    print(f"unknown mode {mode!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
