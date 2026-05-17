#!/usr/bin/env python3
"""Report FastAPI routes missing response_model or explicit status_code."""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TARGETS = ["portal_api"]
HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "trace"}


@dataclass(frozen=True)
class RouteMetadata:
    path: Path
    line: int
    method: str
    route_path: str
    has_response_model: bool
    has_status_code: bool

    @property
    def missing_response_model(self) -> bool:
        return not self.has_response_model

    @property
    def missing_status_code(self) -> bool:
        return not self.has_status_code


def _expand_targets(raw_targets: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in raw_targets:
        path = Path(raw)
        if path.is_dir():
            expanded.extend(sorted(item for item in path.rglob("*.py") if "__pycache__" not in item.parts))
        elif path.suffix == ".py":
            expanded.append(path)

    seen: set[str] = set()
    unique: list[Path] = []
    for path in expanded:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _route_decorator(decorator: ast.expr) -> tuple[str, str, bool, bool] | None:
    if not isinstance(decorator, ast.Call):
        return None
    if not isinstance(decorator.func, ast.Attribute):
        return None
    method = decorator.func.attr
    if method not in HTTP_METHODS:
        return None

    route_path = "<dynamic>"
    if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
        route_path = decorator.args[0].value

    keyword_names = {keyword.arg for keyword in decorator.keywords if keyword.arg}
    return method.upper(), route_path, "response_model" in keyword_names, "status_code" in keyword_names


def audit_file(path: Path) -> list[RouteMetadata]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    routes: list[RouteMetadata] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            route = _route_decorator(decorator)
            if route is None:
                continue
            method, route_path, has_response_model, has_status_code = route
            routes.append(
                RouteMetadata(
                    path=path,
                    line=decorator.lineno,
                    method=method,
                    route_path=route_path,
                    has_response_model=has_response_model,
                    has_status_code=has_status_code,
                )
            )

    return sorted(routes, key=lambda route: (str(route.path), route.line, route.method, route.route_path))


def audit_targets(raw_targets: list[str]) -> list[RouteMetadata]:
    routes: list[RouteMetadata] = []
    for target in _expand_targets(raw_targets):
        routes.extend(audit_file(target))
    return sorted(routes, key=lambda route: (str(route.path), route.line, route.method, route.route_path))


def _read_targets_file(path: Path) -> list[str]:
    targets: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        targets.append(line)
    return targets


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def print_report(routes: list[RouteMetadata]) -> None:
    missing_response_model = [route for route in routes if route.missing_response_model]
    missing_status_code = [route for route in routes if route.missing_status_code]

    print("FastAPI route metadata audit")
    print(f"Routes scanned: {len(routes)}")
    print(f"Missing response_model: {len(missing_response_model)}")
    print(f"Missing explicit status_code: {len(missing_status_code)}")

    if not routes:
        return

    print("")
    print("| File | Line | Method | Route | response_model | status_code |")
    print("|---|---:|---|---|---|---|")
    for route in routes:
        response_model = "yes" if route.has_response_model else "missing"
        status_code = "yes" if route.has_status_code else "missing"
        print(
            f"| {_relative(route.path)} | {route.line} | {route.method} | "
            f"`{route.route_path}` | {response_model} | {status_code} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*")
    parser.add_argument(
        "--targets-file",
        type=Path,
        help="Optional newline-delimited target file. Blank lines and # comments are ignored.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit non-zero when any scanned route is missing response_model or status_code.",
    )
    args = parser.parse_args()
    targets = list(args.targets)
    if args.targets_file:
        targets.extend(_read_targets_file(args.targets_file))
    if not targets:
        targets = DEFAULT_TARGETS

    try:
        routes = audit_targets(targets)
    except SyntaxError as exc:
        print(f"Route metadata audit failed to parse {exc.filename}: {exc.msg}", file=sys.stderr)
        return 2

    print_report(routes)
    if args.fail_on_missing and any(route.missing_response_model or route.missing_status_code for route in routes):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
