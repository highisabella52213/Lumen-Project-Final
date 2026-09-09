# Lumen v27 — Railway-safe project names

- Generates project names as lowercase Railway-safe slugs using only `a-z`, `0-9`, and hyphens.
- Enforces a hard maximum of 32 characters while preserving a compact unique deployment suffix.
- Removes spaces, uppercase letters, underscores, Unicode, and trailing separators from generated project names.
- Retries `projectCreate` once with a minimal randomized slug if Railway returns `Invalid project name`.
- Keeps the v26 Workspace-first flow and always passes the resolved `workspaceId`.
