#!/usr/bin/env python3
"""Regression coverage for subgroup membership and rollback-safe persistence."""

import ast
import asyncio
import copy
import json
from pathlib import Path

source_path = Path(__file__).resolve().parents[1] / "main.py"
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source)
names = {"_normalized_link_ids", "update_sub_group"}
nodes = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names
]

LINKS = {}
SUBS = {}
LINKS_LOCK = asyncio.Lock()
SUBS_LOCK = asyncio.Lock()
STATE_MUTATION_LOCK = asyncio.Lock()
saved = []


async def save_state(*, strict=False, rotate=True):
    saved.append(copy.deepcopy({"links": LINKS, "subs": SUBS}))
    return True


def hash_password(value):
    return "hash:" + value


def log_activity(*args, **kwargs):
    pass


ns = {
    "LINKS": LINKS,
    "SUBS": SUBS,
    "LINKS_LOCK": LINKS_LOCK,
    "SUBS_LOCK": SUBS_LOCK,
    "STATE_MUTATION_LOCK": STATE_MUTATION_LOCK,
    "save_state": save_state,
    "hash_password": hash_password,
    "log_activity": log_activity,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), ns)


async def run():
    group_a, group_b = "group-a", "group-b"
    link_a, link_b, link_c = "link-a", "link-b", "link-c"
    SUBS.update({
        group_a: {"name": "Group A", "link_ids": [link_a]},
        group_b: {"name": "Group B", "link_ids": [link_b]},
    })
    LINKS.update({
        link_a: {"label": "A", "sub_id": group_a},
        link_b: {"label": "B", "sub_id": group_b},
        link_c: {"label": "C", "sub_id": None},
    })

    # Replacing A's selection must not detach B from its unrelated group.
    await ns["update_sub_group"](group_a, {"link_ids": [link_c, link_c]})
    assert LINKS[link_a]["sub_id"] is None
    assert LINKS[link_b]["sub_id"] == group_b
    assert LINKS[link_c]["sub_id"] == group_a
    assert SUBS[group_a]["link_ids"] == [link_c]
    assert SUBS[group_b]["link_ids"] == [link_b]

    # Moving one config removes it from the previous group exactly once.
    await ns["update_sub_group"](group_a, {"link_ids": [link_b, link_c]})
    assert LINKS[link_b]["sub_id"] == group_a
    assert SUBS[group_a]["link_ids"] == [link_b, link_c]
    assert SUBS[group_b]["link_ids"] == []

    before = json.dumps({"links": LINKS, "subs": SUBS}, sort_keys=True)
    try:
        await ns["update_sub_group"](group_a, {"link_ids": ["missing-link"]})
    except ValueError:
        pass
    else:
        raise AssertionError("unknown link id was accepted")
    assert json.dumps({"links": LINKS, "subs": SUBS}, sort_keys=True) == before

    # A persistence failure rolls the in-memory transaction back as well.
    real_save = ns["save_state"]

    async def fail_save(*, strict=False, rotate=True):
        raise RuntimeError("synthetic disk failure")

    ns["save_state"] = fail_save
    try:
        try:
            await ns["update_sub_group"](group_a, {"name": "Should roll back", "link_ids": []})
        except RuntimeError:
            pass
        else:
            raise AssertionError("persistence failure was swallowed")
    finally:
        ns["save_state"] = real_save
    assert json.dumps({"links": LINKS, "subs": SUBS}, sort_keys=True) == before

    assert saved and set(saved[-1]["links"]) == {link_a, link_b, link_c}
    assert set(saved[-1]["subs"]) == {group_a, group_b}

    list_node = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_subs")
    list_source = ast.get_source_segment(source, list_node)
    assert 's["uuid_key"]' in list_source or "s['uuid_key']" in list_source


asyncio.run(run())
print("subgroup v28: unrelated-preserved=OK move=OK dedupe=OK validation=OK rollback=OK list=OK persistence=OK")