import tomli
from typing import List
from pathlib import Path
from anvil.core.parsers.base import BaseParser
from anvil.core.models import Dependency

class PyProjectParser(BaseParser):
    """Parser for pyproject.toml files (poetry/uv/standard)."""

    def can_handle(self) -> bool:
        return self.file_path.name == "pyproject.toml"

    def parse(self) -> List[Dependency]:
        if not self.file_path.exists():
            return []
        
        dependencies = []
        with open(self.file_path, "rb") as f:
            data = tomli.load(f)
            
        # 1. Standard [project.dependencies]
        if "project" in data and "dependencies" in data["project"]:
            for dep_str in data["project"]["dependencies"]:
                # Parse standard requirement string
                # e.g., "requests>=2.0.0"
                # Reuse logic or simple parsing
                dep = self._parse_standard_dep(dep_str)
                if dep:
                    dependencies.append(dep)
                    
        # 2. Poetry [tool.poetry.dependencies]
        if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
            poetry_deps = data["tool"]["poetry"]["dependencies"]
            for name, spec in poetry_deps.items():
                if name == "python":
                    continue
                # Handle object specifiers e.g. {version = "^1.2.3", python = ">=3.9"}
                spec_str = spec
                if isinstance(spec, dict):
                    spec_str = spec.get("version", "")
                
                dependencies.append(Dependency(
                    name=name,
                    current_version=None, # Poetry often uses carets, so current is ambiguous without lock file
                    specifier=str(spec_str),
                    source_file=str(self.file_path),
                    line_number=None # TOML parsing doesn't give lines easily
                ))

        return dependencies

    def _parse_standard_dep(self, dep_str: str) -> Dependency:
        import re
        # Simple extraction similar to requirements.txt
        match = re.match(r'^([a-zA-Z0-9_\-\.]+)(.*)$', dep_str)
        if not match:
            return None
        
        name = match.group(1)
        specifier = match.group(2).strip()
        
        current_version = None
        if '==' in specifier:
             parts = specifier.split('==')
             if len(parts) > 1:
                 version_part = parts[1].split(';')[0].split('#')[0].strip()
                 current_version = version_part
                 
        return Dependency(
            name=name,
            current_version=current_version,
            specifier=specifier,
            source_file=str(self.file_path),
            line_number=None
        )
