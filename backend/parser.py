import re
from typing import Iterable, Set, Tuple


GITHUB_RE = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/|$)",
    re.IGNORECASE,
)


def extract_github_repos_from_markdown(md: str) -> Set[Tuple[str, str]]:
    repos: Set[Tuple[str, str]] = set()
    for owner, name in GITHUB_RE.findall(md or ""):
        owner = owner.strip()
        name = name.strip()
        if owner and name:
            repos.add((owner, name))
    return repos


def normalize_repo(owner: str, name: str) -> str:
    return f"https://github.com/{owner}/{name}"


def iter_repo_links(repo_pairs: Iterable[Tuple[str, str]]) -> Iterable[str]:
    for owner, name in repo_pairs:
        yield normalize_repo(owner, name)
