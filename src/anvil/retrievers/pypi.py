import requests
from typing import Optional, Dict, Any
from anvil.retrievers.base import BaseRetriever

class PyPIRetriever(BaseRetriever):
    """Fetches metadata from PyPI."""
    
    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        # PyPI 'description' field sometimes contains changelog, but it's unreliable for diffs.
        # This retriever focuses on finding the source URL to delegate to GitHubRetriever
        return None

    def get_source_url(self, package_name: str) -> Optional[str]:
        data = self._fetch_pypi_json(package_name)
        if not data:
            return None
            
        info = data.get("info", {})
        project_urls = info.get("project_urls") or {}
        
        # Check common keys for source
        # Normalize keys to lowercase for case-insensitive matching
        urls_lower = {k.lower(): v for k, v in project_urls.items()}
        
        candidates = [
            "source", "source code", "repository", "code", 
            "home", "homepage", 
            "issue tracker", "tracker", "bug tracker"
        ]
        
        for key in candidates:
            url = urls_lower.get(key)
            if url and "github.com" in url:
                return self._clean_github_url(url)
                
        # Check 'home_page' field if not in project_urls
        home_page = info.get("home_page")
        if home_page and "github.com" in home_page:
            return self._clean_github_url(home_page)
            
        return None

    def _fetch_pypi_json(self, package_name: str) -> Optional[Dict[str, Any]]:
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            pass
        return None
        
    def _clean_github_url(self, url: str) -> str:
        # Normalize: https://github.com/user/repo -> https://github.com/user/repo
        # Remove .git, trailing slashes
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        return url
