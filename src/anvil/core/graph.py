from importlib import metadata
from typing import Dict, List, Set
from packaging.requirements import Requirement
from anvil.core.logging import get_logger

logger = get_logger("graph")

class DependencyGraph:
    """
    Builds a directed graph of installed dependencies to detect conflicts.
    """
    def __init__(self):
        self.adj_list: Dict[str, List[str]] = {} # Who does X depend on?
        self.reverse_adj: Dict[str, List[str]] = {} # Who depends on X?
        self._built = False

    def build(self):
        """Builds the graph from the current environment."""
        if self._built:
            return

        logger.info("Building dependency graph...")
        dists = list(metadata.distributions())
        for dist in dists:
            name = dist.metadata["Name"].lower()
            requires = dist.requires or []
            
            for req_str in requires:
                try:
                    req = Requirement(req_str)
                    target = req.name.lower()
                    
                    # Add edge: Name -> Target
                    logger.debug(f"Graph Edge: {name} -> {target}")
                    self.add_edge(name, target)
                except Exception as e:
                    logger.debug(f"Failed to parse requirement '{req_str}' for {name}: {e}")
        
        self._built = True
        logger.info(f"Graph built with {len(self.adj_list)} nodes.")

    def add_edge(self, source: str, target: str):
        if source not in self.adj_list:
            self.adj_list[source] = []
        self.adj_list[source].append(target)
        
        if target not in self.reverse_adj:
            self.reverse_adj[target] = []
        self.reverse_adj[target].append(source)

    def get_dependents(self, package_name: str) -> List[str]:
        """Returns list of packages that depend on 'package_name'."""
        if not self._built:
            self.build()
        return self.reverse_adj.get(package_name.lower(), [])
