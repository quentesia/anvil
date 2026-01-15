import re
from typing import List, Optional
from pathlib import Path
from anvil.core.parsers.base import BaseParser
from anvil.core.models import Dependency

class RequirementsParser(BaseParser):
    """Parser for requirements.txt files."""
    
    def can_handle(self) -> bool:
        return self.file_path.name == "requirements.txt" or self.file_path.suffix == ".txt"

    def parse(self) -> List[Dependency]:
        dependencies = []
        if not self.file_path.exists():
            return []
            
        with open(self.file_path, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle -r includes (skip for now or handle recursively? Skipping for MVP)
                if line.startswith('-r'):
                    continue
                    
                dep = self._parse_line(line, i)
                if dep:
                    dependencies.append(dep)
        return dependencies

    def _parse_line(self, line: str, line_number: int) -> Optional[Dependency]:
        # Basic regex for parsing requirements
        # Handles: package==1.2.3, package>=1.2.3, package, etc.
        # Does not handle advanced markers fully yet
        
        # Regex to capture name and specifier
        # Keep it simple: name [specifier]
        match = re.match(r'^([a-zA-Z0-9_\-\.]+)(.*)$', line)
        if not match:
            return None
            
        name = match.group(1)
        specifier = match.group(2).strip()
        
        # Extract version if it's exact match (==)
        current_version = None
        if '==' in specifier:
             # simplistic extraction: split by == and take the first part after it
             parts = specifier.split('==')
             if len(parts) > 1:
                 # Clean up any other markers like ; or #
                 version_part = parts[1].split(';')[0].split('#')[0].strip()
                 current_version = version_part

        return Dependency(
            name=name,
            current_version=current_version,
            specifier=specifier,
            source_file=str(self.file_path),
            line_number=line_number
        )
