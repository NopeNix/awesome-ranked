from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RepoLatestSnapshot(BaseModel):
    repository_id: int
    owner: str
    name: str
    html_url: str
    repo_created_at: Optional[datetime] = None
    github_default_branch: Optional[str] = None

    stars: int = 0
    forks: int = 0
    watchers: int = 0
    contributors_count_approx: Optional[int] = None
    contributors_sample_size: Optional[int] = None
    commit_count_default_branch: Optional[int] = None
    last_commit_date: Optional[datetime] = None
    last_commit_sha: Optional[str] = None


class RepoListResponse(BaseModel):
    total: int
    items: List[RepoLatestSnapshot]


class RepoSnapshot(BaseModel):
    scraped_at: datetime
    stars: int
    forks: int
    watchers: int
    contributors_count_approx: Optional[int] = None
    contributors_sample_size: Optional[int] = None
    commit_count_default_branch: Optional[int] = None
    last_commit_date: Optional[datetime] = None
    last_commit_sha: Optional[str] = None


class RepoSnapshotsResponse(BaseModel):
    owner: str
    name: str
    html_url: str
    items: List[RepoSnapshot]
