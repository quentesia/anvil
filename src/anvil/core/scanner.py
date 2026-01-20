import ast
import os
from pathlib import Path
from typing import Dict, Set, List, Optional
from anvil.core.logging import get_logger

logger = get_logger("core.scanner")

class ImportVisitor(ast.NodeVisitor):
    """
    AST Visitor to collect imports and their usages.
    """
    def __init__(self):
        self.imports = {}  # alias -> real_name (e.g., 'pd' -> 'pandas')
        self.usages = []   # List of strings (e.g., 'pandas.read_csv', 'pd.DataFrame')
        
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name
            self.imports[asname] = name
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name
            full_name = f"{module}.{name}" if module else name
            self.imports[asname] = full_name
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Handle obj.attr expression
        # We try to resolve the left side (value) to a known import
        try:
            # Simple case: look for Name.Attribute (e.g. pd.read_csv)
            if isinstance(node.value, ast.Name):
                obj_name = node.value.id
                if obj_name in self.imports:
                    real_pkg = self.imports[obj_name]
                    usage = f"{obj_name}.{node.attr}"
                    # We store it as alias usage, but caller can map back
                    self.usages.append(usage)
            # Nested case: obj.attr.attr (e.g. django.db.models)
            # This is harder to do perfectly without recursion, staying simple for now.
        except Exception:
            pass
        self.generic_visit(node)
        
    def visit_Call(self, node):
        # Handle function calls func()
        if isinstance(node.func, ast.Name):
             func_name = node.func.id
             if func_name in self.imports:
                 self.usages.append(f"{func_name}()")
        self.generic_visit(node)

class CodebaseScanner:
    """
    Scans a project directory for Python files and extracts usage of dependencies.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ignore_dirs = {'.venv', 'venv', '.git', '__pycache__', 'node_modules', 'dist', 'build'}

    def scan_package_usage(self, package_name: str) -> List[str]:
        """
        Returns a list of unique usages of the given package found in the codebase.
        e.g., ['pandas.read_csv', 'pd.DataFrame']
        """
        all_usages = set()
        
        logger.debug(f"Scanning codebase for usage of {package_name}...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip ignored
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    usage_in_file = self._scan_file(full_path, package_name)
                    all_usages.update(usage_in_file)
                    
        return sorted(list(all_usages))

    def _scan_file(self, file_path: str, target_package: str) -> Set[str]:
        found = set()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            visitor = ImportVisitor()
            visitor.visit(tree)
            
            # Filter usages related to target_package
            # 1. Check if package is imported
            relevant_aliases = set()
            for alias, real_name in visitor.imports.items():
                # Check if 'pandas' is in 'pandas.core.frame' or 'pandas' == 'pandas'
                if real_name == target_package or real_name.startswith(f"{target_package}."):
                    relevant_aliases.add(alias)
            
            if not relevant_aliases:
                return set()
                
            # 2. Find attributes/calls using those aliases
            for usage in visitor.usages:
                # usage is like "pd.read_csv" or "json.load"
                base = usage.split('.')[0]
                if base in relevant_aliases:
                    found.add(usage)
            
            # 3. Add bare references from ImportFrom (e.g. from foo import bar -> bar used)
            # This is implicit in the visitor.imports map check above? 
            # Actually weak point: if I do `from foo import bar`, usages might be just `bar()`
            # visitor.usages would catch `bar()`.
            # visitor.imports has 'bar' -> 'foo.bar'.
            # aliases has 'bar'.
            # usage 'bar()' base is 'bar'. 'bar' in aliases. YES.
            
        except Exception as e:
            # logger.debug(f"Failed to scan {file_path}: {e}")
            pass
            
        return found
