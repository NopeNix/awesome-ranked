from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from typing import Optional

from database import ensure_schema, session_scope
from schemas import RepoListResponse, RepoLatestSnapshot, RepoSnapshotsResponse, RepoSnapshot
from database import Repository, RepositorySnapshot

app = FastAPI(title="Awesome Ranked API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    ensure_schema()


SORT_MAP = {
    "stars": "ls.stars",
    "forks": "ls.forks",
    "watchers": "ls.watchers",
    "contributors": "ls.contributors_count_approx",
    "commits": "ls.commit_count_default_branch",
    "last_commit": "ls.last_commit_date",
    "created": "r.repo_created_at",
}


@app.get("/api/repos", response_model=RepoListResponse)
def list_repos(
    sortBy: str = "stars",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
):
    sort_col = SORT_MAP.get(sortBy, SORT_MAP["stars"])
    order_dir = "ASC" if order.lower() == "asc" else "DESC"
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    # Latest snapshot per repository (subquery join) + stable ordering.
    # We embed ORDER BY directly into the SQL string because SQLAlchemy's
    # TextClause objects are not addable.
    sql = f"""
        WITH latest_snap AS (
          SELECT rs.*
          FROM repository_snapshots rs
          JOIN (
            SELECT repository_id, MAX(scraped_at) AS max_scraped_at
            FROM repository_snapshots
            GROUP BY repository_id
          ) m
            ON m.repository_id = rs.repository_id AND m.max_scraped_at = rs.scraped_at
        )
        SELECT
          r.id AS repository_id,
          r.owner,
          r.name,
          r.html_url,
          r.repo_created_at,
          r.github_default_branch,
          COALESCE(ls.stars, 0) AS stars,
          COALESCE(ls.forks, 0) AS forks,
          COALESCE(ls.watchers, 0) AS watchers,
          ls.contributors_count_approx,
          ls.contributors_sample_size,
          ls.commit_count_default_branch,
          ls.last_commit_date,
          ls.last_commit_sha
        FROM repositories r
        LEFT JOIN latest_snap ls ON ls.repository_id = r.id
        WHERE r.tracked = true
        ORDER BY {sort_col} {order_dir} NULLS LAST, r.owner ASC, r.name ASC
        LIMIT :limit OFFSET :offset
    """

    count_sql = text(
        """
        SELECT COUNT(*)
        FROM repositories r
        WHERE r.tracked = true
        """
    )

    with session_scope() as db:
        total = db.execute(count_sql).scalar_one()
        rows = db.execute(text(sql), {"limit": limit, "offset": offset}).mappings().all()

    items = [
        RepoLatestSnapshot(
            repository_id=row["repository_id"],
            owner=row["owner"],
            name=row["name"],
            html_url=row["html_url"],
            repo_created_at=row["repo_created_at"],
            github_default_branch=row["github_default_branch"],
            stars=row["stars"],
            forks=row["forks"],
            watchers=row["watchers"],
            contributors_count_approx=row["contributors_count_approx"],
            contributors_sample_size=row["contributors_sample_size"],
            commit_count_default_branch=row["commit_count_default_branch"],
            last_commit_date=row["last_commit_date"],
            last_commit_sha=row["last_commit_sha"],
        )
        for row in rows
    ]
    return RepoListResponse(total=total, items=items)


@app.get("/api/repos/{repo_id}/snapshots", response_model=RepoSnapshotsResponse)
def repo_snapshots(repo_id: int, limit: int = 200):
    limit = max(1, min(int(limit), 500))
    with session_scope() as db:
        repo = db.query(Repository).filter(Repository.id == repo_id).one_or_none()
        if not repo:
            return RepoSnapshotsResponse(owner="", name="", html_url="", items=[])

        rows = (
            db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repo_id)
            .order_by(RepositorySnapshot.scraped_at.desc())
            .limit(limit)
            .all()
        )

    items = [
        RepoSnapshot(
            scraped_at=r.scraped_at,
            stars=r.stars,
            forks=r.forks,
            watchers=r.watchers,
            contributors_count_approx=r.contributors_count_approx,
            contributors_sample_size=r.contributors_sample_size,
            commit_count_default_branch=r.commit_count_default_branch,
            last_commit_date=r.last_commit_date,
            last_commit_sha=r.last_commit_sha,
        )
        for r in rows
    ]
    return RepoSnapshotsResponse(owner=repo.owner, name=repo.name, html_url=repo.html_url, items=items)
