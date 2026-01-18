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
            # Format: https://github.com/owner/repo/tree/branch/subdir...
            parts = source_url.split("github.com/")
            if len(parts) > 1:
                path_parts = parts[1].split('/')
                if len(path_parts) >= 2:
                    repo_slug = f"{path_parts[0]}/{path_parts[1]}"
                    
                    subdirectory = None
                    # Check for '/tree/{branch}/...' pattern to extract subdir
                    if len(path_parts) > 4 and path_parts[2] == "tree":
                        # path_parts[3] is branch name (e.g. master)
                        # path_parts[4:] is the subdirectory
                        subdirectory = "/".join(path_parts[4:])
                    elif len(path_parts) > 2 and path_parts[2] != "tree":
                         # Sometimes it might just be /owner/repo/subdir directly (less common for browse URLs but possible)
                         subdirectory = "/".join(path_parts[2:])
                         
                    return self.github.get_changelog(repo_slug, current_version, target_version, subdirectory, package_name=package_name)
                
        return None
