import requests
import base64
import os
from typing import Optional
from anvil.retrievers.base import BaseRetriever
from anvil.core.logging import get_logger

logger = get_logger("retriever.github")

class GitHubRetriever(BaseRetriever):
    """Fetches changelogs from GitHub."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        if self.api_token:
            logger.debug("GitHubRetriever initialized with API token")
        else:
            logger.debug("GitHubRetriever initialized without API token (unauthenticated)")
        
    def get_source_url(self, package_name: str) -> Optional[str]:
        return None

    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        repo_slug = package_name
        logger.debug(f"Fetching changelog for {repo_slug} (target version: {target_version})")
        
        # 1. Try Releases
        release_note = self._get_release_note(repo_slug, target_version)
        if release_note:
            logger.debug(f"Found release notes for {target_version}")
            return release_note
            
        # 2. Try CHANGELOG.md file content
        logger.debug(f"No release notes found for {target_version}, trying CHANGELOG files...")
        return self._get_changelog_file(repo_slug)

    def _get_headers(self):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _get_release_note(self, repo_slug: str, version: str) -> Optional[str]:
        tags_to_try = [version, f"v{version}"]
        
        for tag in tags_to_try:
            url = f"https://api.github.com/repos/{repo_slug}/releases/tags/{tag}"
            logger.debug(f"Checking GitHub releases for tag: {tag}")
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("body")
                logger.debug(f"Release lookup for {tag} returned {resp.status_code}")
            except requests.RequestException as e:
                logger.debug(f"GitHub release request failed: {e}")
        return None

    def _get_changelog_file(self, repo_slug: str) -> Optional[str]:
        files = ["CHANGELOG.md", "History.md", "RELEASES.md", "CHANGES.md"]
        
        for filename in files:
            url = f"https://api.github.com/repos/{repo_slug}/contents/{filename}"
            logger.debug(f"Checking for file: {filename}")
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    content = resp.json().get("content", "")
                    if content:
                        logger.debug(f"Successfully retrieved {filename}")
                        return base64.b64decode(content).decode("utf-8", errors="ignore")
                logger.debug(f"File lookup for {filename} returned {resp.status_code}")
            except requests.RequestException as e:
                logger.debug(f"GitHub file request failed: {e}")
                
        return None
