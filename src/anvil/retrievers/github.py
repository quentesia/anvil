import requests
import base64
import os
from typing import Optional
from anvil.retrievers.base import BaseRetriever

class GitHubRetriever(BaseRetriever):
    """Fetches changelogs from GitHub."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        
    def get_source_url(self, package_name: str) -> Optional[str]:
        # GitHub retriever assumes we already know it's a GitHub repo from PyPI
        return None

    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        # This method assumes 'package_name' here is actually the "owner/repo" string
        # or we need to pass the repo slug. 
        # For this design, let's assume the caller resolves the repo slug first.
        repo_slug = package_name # Expected to be "owner/repo"
        
        # 1. Try Releases
        release_note = self._get_release_note(repo_slug, target_version)
        if release_note:
            return release_note
            
        # 2. Try CHANGELOG.md file content
        return self._get_changelog_file(repo_slug)

    def _get_headers(self):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _get_release_note(self, repo_slug: str, version: str) -> Optional[str]:
        # Try exact version tag
        # Tags can be v1.0.0 or 1.0.0
        tags_to_try = [version, f"v{version}"]
        
        for tag in tags_to_try:
            url = f"https://api.github.com/repos/{repo_slug}/releases/tags/{tag}"
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("body")
            except requests.RequestException:
                pass
        return None

    def _get_changelog_file(self, repo_slug: str) -> Optional[str]:
        # Look for common changelog names
        files = ["CHANGELOG.md", "History.md", "RELEASES.md", "CHANGES.md"]
        
        for filename in files:
            url = f"https://api.github.com/repos/{repo_slug}/contents/{filename}"
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    content = resp.json().get("content", "")
                    if content:
                        return base64.b64decode(content).decode("utf-8", errors="ignore")
            except requests.RequestException:
                continue
                
        return None
