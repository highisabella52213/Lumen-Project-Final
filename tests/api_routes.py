"""گارد: هر endpoint که پنل صدا می‌زند باید واقعاً روی app ثبت شده باشد.

بدون نیاز به نصب fastapi کار می‌کند (AST استاتیک).
دلیل وجود: یک بار پنل /api/outbound را صدا می‌زد ولی روت ثبت نشده بود → 404.
"""
import ast
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.py"
PAGES = ROOT / "pages.py"

METHODS = {"get", "post", "patch", "delete", "put", "head", "options", "api_route", "websocket"}

failures = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  " + detail) if detail and not cond else ""))
    if not cond:
        failures.append(name)


def module_level_routes(path):
    """فقط روت‌هایی که در سطح مادول هستند واقعاً ثبت می‌شوند."""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    routes = []
    nested = []

    def collect(node, top):
        for deco in getattr(node, "decorator_list", []):
            if not isinstance(deco, ast.Call):
                continue
            fn = deco.func
            if not isinstance(fn, ast.Attribute) or fn.attr not in METHODS:
                continue
            if not deco.args or not isinstance(deco.args[0], ast.Constant):
                continue
            p = deco.args[0].value
            if not isinstance(p, str):
                continue
            (routes if top else nested).append(p)

    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            collect(n, True)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n not in tree.body:
                collect(n, False)
    return routes, nested


def to_regex(route):
    out = ""
    for part in re.split(r"(\{[^}]*\})", route):
        if part.startswith("{") and part.endswith("}"):
            out += ".*" if ":path" in part else "[^/]+"
        else:
            out += re.escape(part)
    return re.compile("^" + out + "$")


def panel_urls(path):
    text = io.open(path, encoding="utf-8").read()
    found = set()
    for pat in (r"authF\(\s*'([^']+)'", r"fetch\(\s*'([^']+)'", r"authF\(\s*`([^`]+)`", r"fetch\(\s*`([^`]+)`"):
        for m in re.finditer(pat, text):
            u = m.group(1)
            if u.startswith("/api/") or u.startswith("/stats"):
                found.add(u)
    return sorted(found)


routes, nested = module_level_routes(MAIN)
regexes = [(r, to_regex(r)) for r in routes]
urls = panel_urls(PAGES)

print("registered module-level routes: %d" % len(routes))
print("panel-called api urls        : %d" % len(urls))
print()

print("[panel -> server route coverage]")
for u in urls:
    if u.endswith("/"):
        hit = any(rx.match(u + "X") for _, rx in regexes)
    else:
        hit = any(rx.match(u) for _, rx in regexes)
    check("panel calls " + u, hit, "-> NO REGISTERED ROUTE (would 404)")

print()
print("[proxy repository endpoints present]")
for need in ("/api/proxy-catalog", "/api/proxy-catalog/refresh"):
    check("route " + need, need in routes)

print()
print("[no api route hidden inside a function]")
bad = [p for p in nested if p.startswith("/api/")]
check("no nested /api routes", not bad, str(bad))

print()
if failures:
    print("FAILURES: %d -> %s" % (len(failures), failures))
    sys.exit(1)
print("api routes: ALL OK")
