"""GitHub release updater for Lumen Railway deployments.

Installer-provisioned credentials are read from protected Railway variables.
Manual deployments can validate and store the same variables from the authenticated
Lumen settings page. Secret values are never returned by the API or written to logs.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

CURRENT_VERSION = "20.0.0"
UPSTREAM_REPOSITORY = "highisabella52213/Lumen-Project-Final"
GITHUB_API = "https://api.github.com"
RAILWAY_GRAPHQL = "https://backboard.railway.com/graphql/v2"
CHECK_SECONDS = 5 * 60
MAX_RESPONSE_BYTES = 1024 * 1024
_apply_lock = asyncio.Lock()
_setup_lock = asyncio.Lock()
_cache = {"at": 0.0, "value": None}


class UpdateError(RuntimeError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def configure(*_args, **_kwargs) -> None:
    """Retained for compatibility with older startup code."""


def _repository(value: str, *, field: str) -> str:
    value = str(value or "").strip().strip("/")
    if value.startswith("https://github.com/"):
        value = value[len("https://github.com/"):]
    if value.endswith(".git"):
        value = value[:-4]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise UpdateError(field + " must use owner/repository format")
    return value


def _branch(value: str) -> str:
    value = str(value or "main").strip()
    if not value or len(value) > 200 or value.startswith(("-", ".")) or ".." in value or re.search(r"[\s~^:?*\\\[]", value):
        raise UpdateError("Invalid Git branch")
    return value


def _token(value: object, *, field: str) -> str:
    token = str(value or "").strip()
    if len(token) < 20 or len(token) > 600 or re.search(r"[\x00-\x1f\x7f]", token):
        raise UpdateError(field + " token format is invalid")
    return token


def _github_token() -> str:
    return str(os.environ.get("LUMEN_GITHUB_TOKEN", "")).strip()


def _railway_token() -> str:
    return str(os.environ.get("LUMEN_RAILWAY_TOKEN", "")).strip()


def _detected_fork() -> str:
    explicit = str(os.environ.get("LUMEN_FORK_REPO", "")).strip()
    if explicit:
        return explicit
    owner = str(os.environ.get("RAILWAY_GIT_REPO_OWNER", "")).strip()
    name = str(os.environ.get("RAILWAY_GIT_REPO_NAME", "")).strip()
    return owner + "/" + name if owner and name else ""


def _credential_source() -> str:
    source = str(os.environ.get("LUMEN_CREDENTIAL_SOURCE", "")).strip().lower()
    if source:
        return source
    return "environment" if (_github_token() or _railway_token()) else "none"


def setup_status() -> dict:
    fork = _detected_fork()
    branch = str(os.environ.get("RAILWAY_GIT_BRANCH") or os.environ.get("LUMEN_GIT_BRANCH") or "main").strip()
    github_set = bool(_github_token())
    railway_set = bool(_railway_token())
    railway_context = all(os.environ.get(name) for name in ("RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID", "RAILWAY_ENVIRONMENT_ID"))
    source = _credential_source()
    configured = all((github_set, railway_set, fork, railway_context))
    return {
        "configured": bool(configured),
        "current_version": CURRENT_VERSION,
        "upstream_repo": UPSTREAM_REPOSITORY,
        "fork_repo": fork,
        "branch": branch,
        "github_token_set": github_set,
        "railway_token_set": railway_set,
        "credentials_locked": bool(github_set or railway_set),
        "credential_source": source,
        "installed_by_installer": source == "installer",
        "railway_context_detected": bool(railway_context),
        "manual_configuration_available": bool(railway_context),
    }


async def load() -> dict:
    return setup_status()


def _request_json(url: str, *, method: str = "GET", headers: dict | None = None, payload: dict | None = None, timeout: float = 12.0) -> dict:
    merged = {"Accept": "application/json", "User-Agent": "Lumen-Relay-Updater/20"}
    if headers:
        merged.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        merged["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=merged, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise UpdateError("Remote response is too large", 502)
            return json.loads(raw.decode() or "{}")
    except urllib.error.HTTPError as exc:
        try:
            parsed = json.loads(exc.read(MAX_RESPONSE_BYTES).decode())
            detail = parsed.get("message") or parsed.get("error")
        except Exception:
            detail = None
        status = 401 if exc.code in (401, 403) else (409 if exc.code == 409 else 502)
        raise UpdateError(str(detail or ("Remote API returned HTTP " + str(exc.code)))[:220], status) from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise UpdateError("Could not reach update service: " + str(exc)[:160], 502) from None


async def _call(url: str, **kwargs) -> dict:
    return await asyncio.to_thread(_request_json, url, **kwargs)


def _github_headers(token: str = "") -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    return headers


async def _railway(query: str, variables: dict, token: str) -> dict:
    result = await _call(RAILWAY_GRAPHQL, method="POST", headers={"Authorization": "Bearer " + token}, payload={"query": query, "variables": variables})
    errors = result.get("errors")
    if errors:
        message = str(errors[0].get("message") if isinstance(errors, list) and errors and isinstance(errors[0], dict) else errors)
        raise UpdateError("Railway rejected the request: " + message[:180], 502)
    return result.get("data") or {}


async def save_setup(data: dict) -> dict:
    """Validate manual credentials and persist them as Railway service variables.

    Existing installer/environment values are locked by default. The caller must
    explicitly acknowledge the warning with confirm_override=true before replacing
    any protected value. Blank token fields always keep the existing secret.
    """
    global _cache
    data = data if isinstance(data, dict) else {}
    current = setup_status()
    if not current["manual_configuration_available"]:
        raise UpdateError("Railway project, service, or environment context is unavailable")
    if current["credentials_locked"] and not bool(data.get("confirm_override")):
        raise UpdateError("Protected credentials are locked; confirm the replacement warning first", 409)

    github_token = str(data.get("github_token") or "").strip() or _github_token()
    railway_token = str(data.get("railway_token") or "").strip() or _railway_token()
    github_token = _token(github_token, field="GitHub")
    railway_token = _token(railway_token, field="Railway")
    fork = _repository(data.get("fork_repo") or current.get("fork_repo"), field="Fork repository")
    branch = _branch(data.get("branch") or current.get("branch"))

    repo_info = await _call(GITHUB_API + "/repos/" + fork, headers=_github_headers(github_token))
    full_name = str(repo_info.get("full_name") or "")
    parent = str((repo_info.get("parent") or {}).get("full_name") or "")
    if full_name.lower() != fork.lower():
        raise UpdateError("GitHub token cannot access the selected repository", 403)
    if fork.lower() != UPSTREAM_REPOSITORY.lower() and (not repo_info.get("fork") or parent.lower() != UPSTREAM_REPOSITORY.lower()):
        raise UpdateError("Selected repository is not the official source or its direct fork")
    await _railway("query LumenCredentialIdentity { me { id name email } }", {}, railway_token)

    project_id = str(os.environ.get("RAILWAY_PROJECT_ID", ""))
    service_id = str(os.environ.get("RAILWAY_SERVICE_ID", ""))
    environment_id = str(os.environ.get("RAILWAY_ENVIRONMENT_ID", ""))
    previous_source = current.get("credential_source")
    source = "manual_override" if previous_source in {"installer", "environment", "manual", "manual_override"} else "manual"
    variables = {
        "LUMEN_UPSTREAM_REPO": UPSTREAM_REPOSITORY,
        "LUMEN_FORK_REPO": fork,
        "LUMEN_GITHUB_TOKEN": github_token,
        "LUMEN_RAILWAY_TOKEN": railway_token,
        "RAILWAY_GIT_BRANCH": branch,
        "LUMEN_CREDENTIAL_SOURCE": source,
    }
    mutation = "mutation SaveLumenCredentials($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }"
    async with _setup_lock:
        await _railway(mutation, {"input": {"projectId": project_id, "environmentId": environment_id, "serviceId": service_id, "variables": variables, "skipDeploys": True, "replace": False}}, railway_token)
        for name, value in variables.items():
            os.environ[name] = value
        _cache = {"at": 0.0, "value": None}
    return setup_status()


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?", str(value or ""))
    if not match:
        raise UpdateError("Latest release tag does not contain a valid version", 502)
    return tuple(int(x or 0) for x in match.groups())


async def check_latest(force: bool = False) -> dict:
    global _cache
    now = time.monotonic()
    if not force and _cache.get("value") is not None and now - float(_cache.get("at") or 0) < CHECK_SECONDS:
        return dict(_cache["value"])
    release = await _call(GITHUB_API + "/repos/" + UPSTREAM_REPOSITORY + "/releases/latest", headers=_github_headers(_github_token()))
    tag = str(release.get("tag_name") or release.get("name") or "")
    latest = ".".join(str(x) for x in _version_tuple(tag))
    setup = setup_status()
    value = {
        **setup,
        "latest_version": latest,
        "tag": tag,
        "available": _version_tuple(latest) > _version_tuple(CURRENT_VERSION),
        "release_url": str(release.get("html_url") or ""),
        "published_at": str(release.get("published_at") or ""),
    }
    _cache = {"at": now, "value": value}
    return dict(value)


async def apply_latest(state_snapshot: str = "") -> dict:
    setup = setup_status()
    if not setup["configured"]:
        raise UpdateError("Complete update credentials in Settings first")
    github_token = _github_token()
    railway_token = _railway_token()
    fork = _repository(setup["fork_repo"], field="Fork repository")
    branch = _branch(setup["branch"])
    project_id = str(os.environ.get("RAILWAY_PROJECT_ID", ""))
    service_id = str(os.environ.get("RAILWAY_SERVICE_ID", ""))
    environment_id = str(os.environ.get("RAILWAY_ENVIRONMENT_ID", ""))

    async with _apply_lock:
        latest = await check_latest(force=True)
        if not latest.get("available"):
            return {"started": False, "already_current": True, **latest}
        repo_info = await _call(GITHUB_API + "/repos/" + fork, headers=_github_headers(github_token))
        parent = str((repo_info.get("parent") or {}).get("full_name") or "")
        if fork.lower() != UPSTREAM_REPOSITORY.lower() and (not repo_info.get("fork") or parent.lower() != UPSTREAM_REPOSITORY.lower()):
            raise UpdateError("Configured repository is not a fork of the official source")
        if fork.lower() != UPSTREAM_REPOSITORY.lower():
            await _call(GITHUB_API + "/repos/" + fork + "/merge-upstream", method="POST", headers=_github_headers(github_token), payload={"branch": branch})
        commit = await _call(GITHUB_API + "/repos/" + fork + "/commits/" + urllib.parse.quote(branch, safe=""), headers=_github_headers(github_token))
        sha = str(commit.get("sha") or "")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise UpdateError("GitHub did not return a valid branch commit", 502)
        if state_snapshot:
            snapshot_mutation = "mutation PersistLumenState($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }"
            await _railway(snapshot_mutation, {"input": {"projectId": project_id, "environmentId": environment_id, "serviceId": service_id, "variables": {"LUMEN_STATE_SNAPSHOT_B64": state_snapshot}, "skipDeploys": True, "replace": False}}, railway_token)
        mutation = "mutation DeployLumenUpdate($serviceId: String!, $environmentId: String!, $commitSha: String!) { serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId, commitSha: $commitSha) }"
        variables = {"serviceId": service_id, "environmentId": environment_id, "commitSha": sha}
        last_error = None
        for attempt in range(3):
            try:
                deployment = await _railway(mutation, variables, railway_token)
                return {"started": True, "version": latest.get("latest_version"), "commit": sha[:12], "deployment": deployment.get("serviceInstanceDeployV2")}
            except UpdateError as exc:
                last_error = exc
                if attempt < 2 and "commit" in str(exc).lower():
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                raise
        raise last_error or UpdateError("Railway deployment failed", 502)
