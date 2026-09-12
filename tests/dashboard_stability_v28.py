#!/usr/bin/env python3
"""Regression contract for the dashboard reload loop and optional catalog."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pages = (root / "pages.py").read_text(encoding="utf-8")
main = (root / "main.py").read_text(encoding="utf-8")

assert "redirectToLoginOnce" in pages
assert "Authentication redirect suppressed to prevent a reload loop" in pages
assert "Session check temporarily unavailable" in pages
assert "if(authenticated===false)return" in pages
assert "Managed proxy repository unavailable" not in pages
assert "catalog_snapshot()" in main
assert "return proxy_repository.catalog_snapshot()" in main
assert "Only the exit country is shown." in pages
assert "p.type.toUpperCase()" not in pages

print(
    "dashboard stability: guarded-auth=OK transient-session=OK "
    "nonblocking-catalog=OK country-only=OK"
)