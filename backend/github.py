import os
from datetime import datetime
from typing import Optional, Dict, Any

import httpx


GITHUB_API = "https://api.github.com"


def _gh_token() -> Optional[str]:
    return os.getenv("GITHUB_TOKEN")


def _headers() -> Dict[str, str]:
    h: Dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "awesome-ranked/1.0",
    }
    token = _gh_token()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _parse_datetime(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    # GitHub uses ISO 8601, e.g. 2020-01-01T00:00:00Z
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


async def fetch_repo_basics(client: httpx.AsyncClient, owner: str, name: str) -> Dict[str, Any]:
    url = f"{GITHUB_API}/repos/{owner}/{name}"
    r = await client.get(url, timeout=30)
    if r.status_code == 404:
        raise ValueError("repo_not_found")
    r.raise_for_status()
    data = r.json()
    return {
        "stars": int(data.get("stargazers_count") or 0),
        "forks": int(data.get("forks_count") or 0),
        "watchers": int(data.get("subscribers_count") or 0),
        "repo_created_at": _parse_datetime(data.get("created_at")),
        "github_default_branch": data.get("default_branch"),
    }


async def fetch_last_commit(client: httpx.AsyncClient, owner: str, name: str, default_branch: Optional[str]) -> Dict[str, Any]:
    branch = default_branch or ""
    params = {"sha": branch, "per_page": 1} if branch else {"per_page": 1}
    url = f"{GITHUB_API}/repos/{owner}/{name}/commits"
    # GitHub supports sha param but if branch empty we fall back to latest on default.
    r = await client.get(url, params=params, timeout=30)
    if r.status_code == 404:
        return {"last_commit_date": None, "last_commit_sha": None}
    r.raise_for_status()
    items = r.json() or []
    if not items:
        return {"last_commit_date": None, "last_commit_sha": None}
    c = items[0]
    return {
        "last_commit_date": _parse_datetime(c.get("commit", {}).get("committer", {}).get("date")),
        "last_commit_sha": (c.get("sha") or None),
    }


async def fetch_commit_count_default_branch(client: httpx.AsyncClient, owner: str, name: str, default_branch: Optional[str]) -> Optional[int]:
    # Approximation via GitHub GraphQL: totalCount of commits in the default branch.
    # This is potentially expensive; we keep it in a best-effort mode.
    if not default_branch:
        return None

    url = f"{GITHUB_API}/graphql"
    query = """
      query($owner: String!, $name: String!, $expr: String!) {
        repository(owner: $owner, name: $name) {
          ref(qualifiedName: $expr) {
            target {
              ... on Commit {
                history(first: 1) { totalCount }
              }
            }
          }
        }
      }
    """
    variables = {
        "owner": owner,
        "name": name,
        "expr": f"refs/heads/{default_branch}",
    }

    r = await client.post(url, json={"query": query, "variables": variables}, timeout=30)
    if r.status_code == 404:
        return None
    if r.status_code == 403:
        # rate limited or missing permissions
        return None
    r.raise_for_status()
    payload = r.json()
    repo = payload.get("data", {}).get("repository")
    if not repo:
        return None
    ref = repo.get("ref")
    if not ref:
        return None
    target = ref.get("target")
    if not target:
        return None
    history = target.get("history") or {}
    total = history.get("totalCount")
    return int(total) if total is not None else None


async def fetch_contributors_approx(client: httpx.AsyncClient, owner: str, name: str) -> Dict[str, Optional[int]]:
    # Approximation: use contributors connection totalCount.
    # Store sample size placeholder as we don't paginate here.
    url = f"{GITHUB_API}/graphql"
    query = """
      query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
          collaborators {
            totalCount
          }
          contributors {
            totalCount
          }
        }
      }
    """
    variables = {"owner": owner, "name": name}
    r = await client.post(url, json={"query": query, "variables": variables}, timeout=30)
    if r.status_code in (403, 404):
        return {"contributors_count_approx": None, "contributors_sample_size": None}
    r.raise_for_status()
    payload = r.json()
    repo = payload.get("data", {}).get("repository") or {}

    # Prefer contributors totalCount; collaborators is often smaller.
    contributors_total = repo.get("contributors", {}).get("totalCount")
    # GraphQL returns int; totalCount is lifetime.
    return {
        "contributors_count_approx": int(contributors_total) if contributors_total is not None else None,
        "contributors_sample_size": 0,
    }


async def fetch_repo_metrics(client: httpx.AsyncClient, owner: str, name: str) -> Dict[str, Any]:
    basics = await fetch_repo_basics(client, owner, name)
    default_branch = basics.get("github_default_branch")
    last = await fetch_last_commit(client, owner, name, default_branch)
    # Best-effort expensive fields
    commit_count = await fetch_commit_count_default_branch(client, owner, name, default_branch)
    contrib = await fetch_contributors_approx(client, owner, name)
    return {
        **basics,
        **last,
        "commit_count_default_branch": commit_count,
        **contrib,
    }


"""GitHub scraper helpers.

Best-effort in this implementation: if fields are blocked/rate-limited, we
return null/None for that metric and still record stars/forks/watchers.
"""
