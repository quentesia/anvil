from typing import Optional
from anvil.retrievers.base import BaseRetriever
from anvil.retrievers.pypi import PyPIRetriever
from anvil.retrievers.github import GitHubRetriever

class ChangelogRetriever(BaseRetriever):
    """Facade for retrieving changelogs using multiple strategies."""
    
    def __init__(self):
        self.pypi = PyPIRetriever()
        self.github = GitHubRetriever()
        
    def get_source_url(self, package_name: str) -> Optional[str]:
        return self.pypi.get_source_url(package_name)

    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        # 1. Resolve source URL
        source_url = self.get_source_url(package_name)
        if not source_url:
            return None
            
        # 2. Extract owner/repo from source URL
        # Assumption: source_url is like https://github.com/owner/repo
        if "github.com" in source_url:
            parts = source_url.split("github.com/")
            if len(parts) > 1:
                repo_slug = parts[1]
                return self.github.get_changelog(repo_slug, current_version, target_version)
                
        return None
