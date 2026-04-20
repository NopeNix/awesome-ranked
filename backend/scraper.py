import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

import httpx

from database import session_scope, Repository, RepositorySnapshot
from parser import extract_github_repos_from_markdown
from github import _headers, fetch_repo_metrics


def _parse_interval_hours() -> int:
    try:
        return int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))
    except ValueError:
        return 24


def _source_url() -> str:
    return os.getenv(
        "SCRAPE_SOURCE_URL",
        "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/refs/heads/master/README.md",
    )


async def _fetch_source_markdown(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url, timeout=60)
    r.raise_for_status()
    return r.text


async def upsert_tracked_repos(source_url: str) -> int:
    async with httpx.AsyncClient(headers={"User-Agent": "awesome-ranked/1.0"}) as client:
        md = await _fetch_source_markdown(client, source_url)
    repos: List[Tuple[str, str]] = sorted(extract_github_repos_from_markdown(md))

    inserted = 0
    with session_scope() as db:
        # Keep existing repos, update URL.
        for owner, name in repos:
            html_url = f"https://github.com/{owner}/{name}"
            existing = (
                db.query(Repository)
                .filter(Repository.owner == owner, Repository.name == name)
                .one_or_none()
            )
            if existing:
                existing.html_url = html_url
                existing.tracked = True
            else:
                db.add(Repository(owner=owner, name=name, html_url=html_url, tracked=True))
                inserted += 1
        db.commit()
    return inserted


async def scrape_repo_if_due(
    repo: Repository,
    client: httpx.AsyncClient,
    db,
    scrape_interval_hours: int,
) -> bool:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=scrape_interval_hours)

    latest = (
        db.query(RepositorySnapshot)
        .filter(RepositorySnapshot.repository_id == repo.id)
        .order_by(RepositorySnapshot.scraped_at.desc())
        .first()
    )
    if latest and latest.scraped_at >= cutoff:
        # Snapshots are fresh, but repository metadata may still be missing
        # (e.g. if an earlier version updated detached ORM instances).
        if repo.repo_created_at is not None and repo.github_default_branch is not None:
            return False

    metrics = await fetch_repo_metrics(client, repo.owner, repo.name)
    snapshot = RepositorySnapshot(
        repository_id=repo.id,
        scraped_at=now,
        stars=metrics.get("stars") or 0,
        forks=metrics.get("forks") or 0,
        watchers=metrics.get("watchers") or 0,
        contributors_count_approx=metrics.get("contributors_count_approx"),
        contributors_sample_size=metrics.get("contributors_sample_size"),
        commit_count_default_branch=metrics.get("commit_count_default_branch"),
        last_commit_date=metrics.get("last_commit_date"),
        last_commit_sha=metrics.get("last_commit_sha"),
    )
    db.add(snapshot)
    repo.github_default_branch = metrics.get("github_default_branch")
    repo.repo_created_at = metrics.get("repo_created_at")
    db.commit()
    return True


async def backfill_and_update(source_url: str) -> Dict[str, Any]:
    scrape_interval_hours = _parse_interval_hours()
    concurrency = int(os.getenv("SCRAPE_CONCURRENCY", "2"))

    inserted = await upsert_tracked_repos(source_url)

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=20)
    async with httpx.AsyncClient(headers=_headers(), limits=limits) as client:
        with session_scope() as db:
            repos: List[Repository] = (
                db.query(Repository).filter(Repository.tracked == True).all()  # noqa: E712
            )
        total = len(repos)

        sem = asyncio.Semaphore(concurrency)
        stats: Dict[str, Any] = {
            "total": total,
            "upserted": inserted,
            "scraped": 0,
            "skipped": 0,
            "errors": 0,
        }

        async def worker(repo: Repository):
            async with sem:
                with session_scope() as db:
                    try:
                        db_repo = db.query(Repository).filter(Repository.id == repo.id).one_or_none()
                        if not db_repo:
                            stats["errors"] += 1
                            return

                        # Use db_repo for updates, but keep owner/name from outer
                        # just in case (should already match by id).
                        db_repo.owner = repo.owner
                        db_repo.name = repo.name

                        did = await scrape_repo_if_due(db_repo, client, db, scrape_interval_hours)
                        if did:
                            stats["scraped"] += 1
                        else:
                            stats["skipped"] += 1
                    except ValueError:
                        stats["errors"] += 1
                    except Exception:
                        stats["errors"] += 1

        await asyncio.gather(*(worker(r) for r in repos))
        return stats


def run_once() -> Dict[str, Any]:
    return asyncio.run(backfill_and_update(_source_url()))
