# Lumen v26 — workspace-first Railway projects

- Resolves Railway workspaces before project creation and always passes `workspaceId` to `ProjectCreateInput`.
- Reuses a dedicated `Lumen <GitHub user>` workspace on repeated attempts.
- Discovers `workspaceCreate` through the live GraphQL schema and creates the dedicated workspace when the current Railway API/account supports it.
- If workspace creation is not exposed or the plan disallows it, safely reuses the first accessible workspace.
- Returns a precise `WORKSPACE_REQUIRED` error only when no workspace can be created or accessed.
- Shows the selected workspace and whether it was created or reused on the success screen.
