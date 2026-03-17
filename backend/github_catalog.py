from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

import requests


@dataclass(slots=True)
class GitHubRepo:
    repo_id: int
    name: str
    full_name: str
    owner: str
    private: bool
    default_branch: str
    clone_url: str
    html_url: str
    description: str | None = None

    def to_json(self) -> dict[str, object]:
        return asdict(self)


class GitHubCatalogClient:
    def __init__(self):
        token = (
            os.getenv("GITHUB_TOKEN", "").strip()
            or os.getenv("GH_TOKEN", "").strip()
            or os.getenv("GITHUB_PAT", "").strip()
        )
        self.api_url = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
        self.token = token
        self.per_page = self._resolve_per_page()

    def _resolve_per_page(self) -> int:
        raw = os.getenv("GITHUB_REPOS_PER_PAGE", "50").strip()
        try:
            return max(1, min(100, int(raw)))
        except ValueError:
            return 50

    def is_configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "jarvez-github-catalog",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, path: str, *, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.api_url}{path}",
            params=params or None,
            headers=self._headers(),
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    def list_repos(self, *, visibility: str = "all", limit: int = 20) -> list[GitHubRepo]:
        per_page = max(1, min(self.per_page, limit))
        if not self.is_configured():
            return []
        items = self._request(
            "/user/repos",
            params={
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc",
                "affiliation": "owner,collaborator,organization_member",
                "visibility": visibility if visibility in {"all", "public", "private"} else "all",
            },
        )
        return [self._parse_repo(item) for item in items][:limit]

    def find_repos(self, query: str, *, limit: int = 10) -> list[GitHubRepo]:
        needle = query.strip().casefold()
        if not needle:
            return self.list_repos(limit=limit)

        ranked: list[tuple[int, GitHubRepo]] = []
        for repo in self.list_repos(limit=max(limit * 4, 20)):
            score = 0
            full_name = repo.full_name.casefold()
            name = repo.name.casefold()
            owner = repo.owner.casefold()
            if needle == full_name:
                score += 300
            if needle == name:
                score += 240
            if needle == owner:
                score += 90
            if needle in full_name:
                score += 140
            if needle in name:
                score += 120
            if needle in owner:
                score += 40
            if repo.description and needle in repo.description.casefold():
                score += 30
            if score > 0:
                ranked.append((score, repo))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [repo for _, repo in ranked[:limit]]

    def resolve_repo(self, query: str) -> tuple[GitHubRepo | None, list[GitHubRepo]]:
        candidates = self.find_repos(query, limit=5)
        if not candidates:
            return None, []
        top = candidates[0]
        normalized = query.strip().casefold()
        if normalized in {top.full_name.casefold(), top.name.casefold()}:
            return top, candidates
        if len(candidates) == 1:
            return top, candidates
        return None, candidates

    def _parse_repo(self, item: dict[str, Any]) -> GitHubRepo:
        owner_payload = item.get("owner") if isinstance(item.get("owner"), dict) else {}
        owner = str(owner_payload.get("login", "")).strip() or "unknown"
        return GitHubRepo(
            repo_id=int(item.get("id", 0) or 0),
            name=str(item.get("name", "")).strip(),
            full_name=str(item.get("full_name", "")).strip(),
            owner=owner,
            private=bool(item.get("private", False)),
            default_branch=str(item.get("default_branch", "")).strip() or "main",
            clone_url=str(item.get("clone_url", "")).strip(),
            html_url=str(item.get("html_url", "")).strip(),
            description=str(item.get("description", "")).strip() or None,
        )
