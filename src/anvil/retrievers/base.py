from abc import ABC, abstractmethod
from typing import Optional

class BaseRetriever(ABC):
    """Abstract base class for changelog retrievers."""
    
    @abstractmethod
    def get_changelog(self, package_name: str, current_version: str, target_version: str) -> Optional[str]:
        """
        Retrieves the changelog or release notes for the given package upgrade.
        Returns None if not found.
        """
        pass
        
    @abstractmethod
    def get_source_url(self, package_name: str) -> Optional[str]:
        """
        Retrieves the source code repository URL (e.g. GitHub).
        """
        pass
