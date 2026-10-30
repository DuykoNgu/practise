from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCREENS_DIR = ROOT / "project" / "screens"
TRACKER = ROOT / "project" / "tracker.md"

KINDS = {"screen", "platform", "api", "worker", "ai", "verification"}
TRACKS = {"main", "ai"}
MILESTONES = {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "AI"}
STATUSES = {"todo": "⬜", "in_progress": "🟨", "review": "🟦", "done": "✅", "blocked": "⛔"}
ROLES = {"PUBLIC", "ADMIN", "IT_MANAGER", "CHANGE_ENGINEER", "AGENT", "ITSM", "LOG_SOURCE", "WORKER"}
STATES = {
    "loading",
    "empty",
    "filtered-empty",
    "no-suspect",
    "no-suggestion",
    "no-related-logs",
    "suggestion-label",
    "masked-data",
    "validation-error",
    "api-error",
    "unauthorized",
    "forbidden",
    "conflict",
    "saving",
    "success",
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
ID_PATTERN = re.compile(r"^(PLT-\d+|SCR-\d{2}(\.\d+)?|API-[A-Z]+|JOB-[A-Z]+|AI-\d+|NFR-[A-Z]+)$")
TASK_PATTERN = re.compile(r"^\[( |x)\] \S")
COMMON_KEYS = (
    "id",
    "kind",
    "name",
    "track",
    "milestone",
    "order",
    "depends_on",
    "status",
    "roles",
    "stories",
    "acceptance",
    "rules",
    "nfr",
    "docs",
    "backend",
    "tasks",
    "done_when",
    "open",
)
SCREEN_KEYS = ("covers", "route", "presentation", "frontend")
FRONTEND_KEYS = ("feature", "components", "hooks", "states")
BACKEND_KEYS = ("modules", "api", "tables", "jobs")
AI_KEYS = ("modules", "cli", "datasets", "metrics")
TASK_GROUPS = {"backend", "frontend", "ai", "tests"}


@dataclass
class Catalog:
    stories: set[str]
    acceptance: set[str]
    rules: set[str]
    nfr: set[str]
    questions: set[str]
    screens: set[str]
    metrics: set[str]
    tables: set[str]
    job_types: set[str]
    operations: set[str]
    modules: set[str]
    features: set[str]
    app_tree: str


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)

    def add(self, item_id: str, message: str) -> None:
        self.errors.append(f"{item_id}: {message}")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def ids(text: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, text, flags=re.MULTILINE))


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def load_catalog() -> Catalog:
    sql = read("src/database/cic.sql")
    openapi = yaml.safe_load(read("docs/api/openapi.yaml"))
    folders = read("docs/07-folder-structure.md")
    backend_tree = section(folders, "## 3. Backend", "### Inside a module")
    frontend_tree = section(folders, "## 2. Frontend", "## 3. Backend")
    features_block = section(frontend_tree, "├── features/", "├── components/")
    job_enum = re.search(r"CREATE TYPE job_type\s+AS ENUM \(([^)]*)\)", sql)
    return Catalog(
        stories=ids(section(read("docs/05-invest-requirements.md"), "## Product backlog", "## Per-story"), r"^\| (US\d{2}) \|"),
        acceptance=ids(read("docs/08-acceptance-criteria.md"), r"^## (AC-UC\d{2})"),
        rules=ids(read("docs/requirements/business-rules.md"), r"^### (BR-\d{3})"),
        nfr=ids(read("docs/requirements/non-functional-requirements.md"), r"^\| (NFR-[A-Z0-9]+-\d{3}) \|"),
        questions=ids(read("project/risks-and-questions.md"), r"^\| ([QI]-\d{2}) \|"),
        screens=ids(read("docs/04-information-architecture.md"), r"^\| `(SCR-\d{2})` \|"),
        metrics=ids(read("docs/architecture/ai-package.md"), r"^\| (M-[A-Z]+-\d{2}) \|"),
        tables=set(re.findall(r"CREATE TABLE (\w+)", sql)),
        job_types=set(re.findall(r"'(\w+)'", job_enum.group(1))) if job_enum else set(),
        operations={
            f"{method.upper()} {path}"
            for path, operations in openapi["paths"].items()
            for method in operations
            if method in HTTP_METHODS
        },
        modules=set(re.findall(r"^│   │   [├└]── ([a-z_]+)/", backend_tree, flags=re.MULTILINE)),
        features={
            name for line in features_block.splitlines()[1:] if "(each" not in line for name in re.findall(r"([a-z_]+)/", line)
        },
        app_tree=section(frontend_tree, "├── app/", "├── features/"),
    )


def slug(heading: str) -> str:
    text = unicodedata.normalize("NFKC", heading).strip().lower()
    text = "".join(char for char in text if char.isalnum() or char in " -_")
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    headings = re.findall(r"^#{1,6} (.+)$", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return {slug(heading) for heading in headings}


def load_items(report: Report) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(SCREENS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            report.add(path.name, "file is not a mapping")
            continue
        if data.get("id") != path.stem:
            report.add(path.name, f"id {data.get('id')!r} differs from file name")
        items[path.stem] = data
    return items


def check_keys(item_id: str, item: dict[str, Any], report: Report) -> bool:
    missing = [key for key in COMMON_KEYS if key not in item]
    if item.get("kind") == "screen":
        missing += [key for key in SCREEN_KEYS if key not in item]
        missing += [f"frontend.{key}" for key in FRONTEND_KEYS if key not in (item.get("frontend") or {})]
    if item.get("kind") == "ai":
        missing += [f"ai.{key}" for key in AI_KEYS if key not in (item.get("ai") or {})]
    missing += [f"backend.{key}" for key in BACKEND_KEYS if key not in (item.get("backend") or {})]
    for key in missing:
        report.add(item_id, f"missing key {key}")
    return not missing


def check_values(item_id: str, item: dict[str, Any], catalog: Catalog, report: Report) -> None:
    if not ID_PATTERN.match(item_id):
        report.add(item_id, "id does not follow the naming pattern")
    for key, allowed in (("kind", KINDS), ("track", TRACKS), ("milestone", MILESTONES), ("status", STATUSES)):
        if item[key] not in allowed:
            report.add(item_id, f"{key} {item[key]!r} not in {sorted(allowed)}")
    for action, roles in (item["roles"] or {}).items():
        for role in roles:
            if role.removesuffix(":own") not in ROLES:
                report.add(item_id, f"role {role!r} in {action} is unknown")
    for key, known in (
        ("stories", catalog.stories),
        ("acceptance", catalog.acceptance),
        ("rules", catalog.rules),
        ("nfr", catalog.nfr),
        ("open", catalog.questions),
    ):
        for value in item[key]:
            if value not in known:
                report.add(item_id, f"{key} {value} not found in docs")
    for screen in item.get("covers") or []:
        if screen not in catalog.screens:
            report.add(item_id, f"covers {screen} not in the IA screen inventory")
    check_docs(item_id, item["docs"], report)
    check_backend(item_id, item["backend"], catalog, report)
    if item["kind"] == "screen":
        check_frontend(item_id, item, catalog, report)
    for metric in (item.get("ai") or {}).get("metrics", []):
        if metric not in catalog.metrics:
            report.add(item_id, f"metric {metric} not in ai-package.md")
    check_tasks(item_id, item, report)


def check_docs(item_id: str, docs: list[str], report: Report) -> None:
    for reference in docs:
        path_part, _, anchor = reference.partition("#")
        path = ROOT / path_part
        if not path.exists():
            report.add(item_id, f"doc {path_part} does not exist")
        elif anchor and anchor not in anchors(path):
            report.add(item_id, f"anchor #{anchor} not found in {path_part}")


def check_backend(item_id: str, backend: dict[str, Any], catalog: Catalog, report: Report) -> None:
    for module in backend["modules"]:
        if module not in catalog.modules:
            report.add(item_id, f"backend module {module} not in 07-folder-structure.md")
    for operation in backend["api"]:
        if operation not in catalog.operations:
            report.add(item_id, f"API {operation} not in openapi.yaml")
    for table in backend["tables"]:
        if table not in catalog.tables:
            report.add(item_id, f"table {table} not in cic.sql")
    for job in backend["jobs"]:
        if job not in catalog.job_types:
            report.add(item_id, f"job {job} not in cic.sql job_type")


def check_frontend(item_id: str, item: dict[str, Any], catalog: Catalog, report: Report) -> None:
    frontend = item["frontend"]
    feature = frontend["feature"]
    if feature is not None and feature not in catalog.features:
        report.add(item_id, f"frontend feature {feature} not in 07-folder-structure.md")
    for segment in str(item["route"]).split("/"):
        if f"{segment}/" not in catalog.app_tree:
            report.add(item_id, f"route segment {segment} not in the app tree of 07-folder-structure.md")
    for state in frontend["states"]:
        if state not in STATES:
            report.add(item_id, f"state {state!r} not in the state vocabulary")
    for component in frontend["components"]:
        if not re.match(r"^[A-Z][A-Za-z0-9]+$", component):
            report.add(item_id, f"component {component!r} is not PascalCase")
    for hook in frontend["hooks"]:
        if not re.match(r"^use[A-Z][A-Za-z0-9]+$", hook):
            report.add(item_id, f"hook {hook!r} does not start with use")


def check_tasks(item_id: str, item: dict[str, Any], report: Report) -> None:
    tasks = item["tasks"] or {}
    for group, entries in tasks.items():
        if group not in TASK_GROUPS:
            report.add(item_id, f"task group {group!r} not in {sorted(TASK_GROUPS)}")
        for entry in entries or []:
            if not TASK_PATTERN.match(str(entry)):
                report.add(item_id, f"task {entry!r} must start with '[ ] ' or '[x] '")
    unticked = [entry for entries in tasks.values() for entry in entries or [] if not str(entry).startswith("[x]")]
    if item["status"] == "done" and unticked:
        report.add(item_id, "status done but some tasks are not ticked")


def check_graph(items: dict[str, dict[str, Any]], report: Report) -> None:
    orders: dict[tuple[str, int], str] = {}
    for item_id, item in items.items():
        key = (item["track"], item["order"])
        if key in orders:
            report.add(item_id, f"order {item['order']} already used by {orders[key]} in track {item['track']}")
        orders[key] = item_id
        for dependency in item["depends_on"]:
            if dependency not in items:
                report.add(item_id, f"depends on unknown item {dependency}")
                continue
            other = items[dependency]
            if other["track"] == item["track"] and other["order"] >= item["order"]:
                report.add(item_id, f"depends on {dependency}, which comes later in track {item['track']}")
            if item["status"] in {"in_progress", "review", "done"} and other["status"] != "done":
                report.add(item_id, f"status {item['status']} while dependency {dependency} is {other['status']}")
    visiting: set[str] = set()
    finished: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in finished or node not in items:
            return
        if node in visiting:
            report.add(node, f"dependency cycle {' -> '.join([*path, node])}")
            return
        visiting.add(node)
        for dependency in items[node]["depends_on"]:
            visit(dependency, [*path, node])
        visiting.discard(node)
        finished.add(node)

    for item_id in items:
        visit(item_id, [])


def check_coverage(items: dict[str, dict[str, Any]], catalog: Catalog, report: Report) -> None:
    used: dict[str, set[str]] = defaultdict(set)
    for item in items.values():
        used["story"].update(item["stories"])
        used["acceptance"].update(item["acceptance"])
        used["rule"].update(item["rules"])
        used["nfr"].update(item["nfr"])
        used["screen"].update(item.get("covers") or [])
        used["operation"].update(item["backend"]["api"])
        used["table"].update(item["backend"]["tables"])
        used["module"].update(item["backend"]["modules"])
        used["job"].update(item["backend"]["jobs"])
        used["metric"].update((item.get("ai") or {}).get("metrics", []))
    for label, known in (
        ("story", catalog.stories),
        ("acceptance", catalog.acceptance),
        ("rule", catalog.rules),
        ("nfr", catalog.nfr),
        ("screen", catalog.screens),
        ("operation", catalog.operations),
        ("table", catalog.tables),
        ("module", catalog.modules),
        ("job", catalog.job_types),
        ("metric", catalog.metrics),
    ):
        for value in sorted(known - used[label]):
            report.add("coverage", f"{label} {value} is not covered by any item")


def tasks_progress(item: dict[str, Any]) -> str:
    entries = [str(entry) for group in (item["tasks"] or {}).values() for entry in group or []]
    return f"{sum(entry.startswith('[x]') for entry in entries)}/{len(entries)}"


def render_tracker(items: dict[str, dict[str, Any]], catalog: Catalog) -> str:
    lines = [
        "# Tracker — CIC V1",
        "",
        "> Generated by `python project/tools/check_screens.py --write` from [screens/](screens/README.md). "
        "Edit the YAML files, not this page. Legend: [README](README.md#status-legend).",
        "",
    ]
    for track, title in (("main", "Main track"), ("ai", "AI track")):
        lines += [
            f"## {title}",
            "",
            "| Order | ID | Name | Kind | Milestone | Covers | Depends on | Tasks | Status |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for item in sorted((i for i in items.values() if i["track"] == track), key=lambda i: i["order"]):
            covers = ", ".join(item.get("covers") or []) or "—"
            depends = ", ".join(item["depends_on"]) or "—"
            lines.append(
                f"| {item['order']} | [{item['id']}](screens/{item['id']}.yaml) | {item['name']} | {item['kind']} "
                f"| {item['milestone']} | {covers} | {depends} | {tasks_progress(item)} | {STATUSES[item['status']]} |"
            )
        lines.append("")
    lines += ["## Progress", "", "| Milestone | Items | Done |", "|---|---|---|"]
    for milestone in sorted(MILESTONES, key=lambda m: (m == "AI", m)):
        group = [i for i in items.values() if i["milestone"] == milestone]
        lines.append(f"| {milestone} | {len(group)} | {sum(i['status'] == 'done' for i in group)} |")
    lines.append(f"| **Total** | **{len(items)}** | **{sum(i['status'] == 'done' for i in items.values())}** |")
    lines += ["", "## Stories", "", "| Story | Items | Status |", "|---|---|---|"]
    for story in sorted(catalog.stories):
        owners = sorted((i for i in items.values() if story in i["stories"]), key=lambda i: (i["track"] != "main", i["order"]))
        statuses = {i["status"] for i in owners}
        status = "done" if statuses == {"done"} else "todo" if statuses <= {"todo"} else "in_progress"
        links = ", ".join(f"[{i['id']}](screens/{i['id']}.yaml)" for i in owners)
        lines.append(f"| {story} | {links} | {STATUSES[status]} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate project/screens and regenerate project/tracker.md")
    parser.add_argument("--write", action="store_true", help="regenerate project/tracker.md")
    args = parser.parse_args()
    report = Report()
    catalog = load_catalog()
    items = load_items(report)
    valid = {item_id: item for item_id, item in items.items() if check_keys(item_id, item, report)}
    for item_id, item in valid.items():
        check_values(item_id, item, catalog, report)
    if len(valid) == len(items):
        check_graph(valid, report)
        check_coverage(valid, catalog, report)
    for error in report.errors:
        print(f"✗ {error}")
    if report.errors:
        print(f"\n{len(report.errors)} problem(s) in {len(items)} item(s)")
        return 1
    if args.write:
        TRACKER.write_text(render_tracker(valid, catalog), encoding="utf-8")
        print(f"tracker.md regenerated from {len(valid)} items")
    print(f"✓ {len(valid)} items consistent with docs, OpenAPI, schema, and folder structure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
