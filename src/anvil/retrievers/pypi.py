import requests
from typing import Optional, Dict, Any
from anvil.retrievers.base import BaseRetriever
from anvil.core.logging import get_logger

logger = get_logger("retriever.pypi")

class PyPIRetriever(BaseRetriever):
    """Fetches metadata from PyPI."""
    
    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        return None

    def get_source_url(self, package_name: str) -> Optional[str]:
        logger.debug(f"Searching PyPI for source URL of: {package_name}")
        data = self._fetch_pypi_json(package_name)
        if not data:
            logger.debug(f"No JSON data found for {package_name} on PyPI")
            return None
            
        info = data.get("info", {})
        project_urls = info.get("project_urls") or {}
        
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
                cleaned_url = self._clean_github_url(url)
                logger.debug(f"Matched source URL '{cleaned_url}' via key '{key}'")
                return cleaned_url
                
        # Check 'home_page' field if not in project_urls
        home_page = info.get("home_page")
        if home_page and "github.com" in home_page:
            cleaned_url = self._clean_github_url(home_page)
            logger.debug(f"Matched source URL '{cleaned_url}' via home_page field")
            return cleaned_url
            
        logger.debug(f"No GitHub source URL found in metadata for {package_name}")
        return None

    def _fetch_pypi_json(self, package_name: str) -> Optional[Dict[str, Any]]:
        url = f"https://pypi.org/pypi/{package_name}/json"
        logger.debug(f"Fetching: {url}")
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            logger.debug(f"PyPI returned status code: {resp.status_code}")
        except requests.RequestException as e:
            logger.debug(f"PyPI request failed: {e}")
        return None
        
    def _clean_github_url(self, url: str) -> str:
        # Normalize: https://github.com/user/repo -> https://github.com/user/repo
        # Remove .git, trailing slashes
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        return url
