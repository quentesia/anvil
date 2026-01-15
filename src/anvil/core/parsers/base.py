from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from anvil.core.models import Dependency

class BaseParser(ABC):
    """Abstract base class for dependency parsers."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        
    @abstractmethod
    def parse(self) -> List[Dependency]:
        """Parse the dependency file and return a list of dependencies."""
        pass
    
    @abstractmethod
    def can_handle(self) -> bool:
        """Check if this parser can handle the given file."""
        pass
