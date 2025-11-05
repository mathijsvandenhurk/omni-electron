"""
Repository Scanner - High-level understanding of project structure

This module analyzes the overall structure of a codebase,
identifying core modules, entry points, and dependencies.
"""

import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from collections import Counter
import logging

from .code_indexer import CodeIndexer, FileIndex
from .ast_analyzer import ImportInfo

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a Python module"""
    path: Path
    name: str  # Module name (e.g., "core.llm_client")
    imports: List[str]  # Modules this imports
    exported_symbols: List[str]  # Functions/classes defined here
    is_core: bool = False  # Is this a frequently imported core module?
    import_count: int = 0  # How many files import this
    

@dataclass
class ProjectStats:
    """Overall project statistics"""
    total_modules: int
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    core_modules: List[str]
    entry_points: List[Path]
    circular_dependencies: List[List[str]]
    

@dataclass
class ProjectMap:
    """Complete map of project structure"""
    root: Path
    modules: List[ModuleInfo]
    entry_points: List[Path]
    test_files: List[Path]
    dependency_graph: nx.DiGraph
    stats: ProjectStats
    

class RepoScanner:
    """
    Scans and understands the high-level structure of a codebase.
    
    Identifies:
    - Core modules (most imported)
    - Entry points (main.py, __main__.py, etc.)
    - Test files
    - Module dependencies
    - Circular dependencies
    """
    
    def __init__(self, indexer: CodeIndexer):
        """
        Initialize repository scanner.
        
        Args:
            indexer: CodeIndexer with already-indexed codebase
        """
        self.indexer = indexer
        self.root = indexer.root
        logger.info(f"RepoScanner initialized for {self.root}")
    
    def scan_project(self) -> ProjectMap:
        """
        Build complete map of project structure.
        
        Returns:
            ProjectMap with all project information
        """
        logger.info("Scanning project structure...")
        
        # Build module list
        modules = self._build_module_list()
        
        # Find entry points
        entry_points = self.find_entry_points()
        
        # Find test files
        test_files = self.detect_test_files()
        
        # Build dependency graph
        dep_graph = self.build_module_graph()
        
        # Find circular dependencies
        circular_deps = self.find_circular_dependencies()
        
        # Identify core modules
        core_modules = self.identify_core_modules()
        
        # Calculate stats
        stats = ProjectStats(
            total_modules=len(modules),
            total_files=len(self.indexer.index),
            total_functions=sum(len(idx.functions) for idx in self.indexer.index.values()),
            total_classes=sum(len(idx.classes) for idx in self.indexer.index.values()),
            total_lines=sum(idx.stats.lines_of_code for idx in self.indexer.index.values()),
            core_modules=[m.name for m in core_modules],
            entry_points=entry_points,
            circular_dependencies=circular_deps
        )
        
        project_map = ProjectMap(
            root=self.root,
            modules=modules,
            entry_points=entry_points,
            test_files=test_files,
            dependency_graph=dep_graph,
            stats=stats
        )
        
        logger.info("Project scan complete")
        return project_map
    
    def _build_module_list(self) -> List[ModuleInfo]:
        """Build list of all modules with their information"""
        modules = []
        
        for filepath, file_index in self.indexer.index.items():
            # Calculate module name
            try:
                rel_path = filepath.relative_to(self.root)
                module_name = str(rel_path.with_suffix('')).replace('/', '.')
            except ValueError:
                module_name = filepath.stem
            
            # Extract imports
            imports = [imp.module for imp in file_index.imports]
            
            # Extract exported symbols
            exported_symbols = []
            exported_symbols.extend([func.name for func in file_index.functions])
            exported_symbols.extend([cls.name for cls in file_index.classes])
            
            module_info = ModuleInfo(
                path=filepath,
                name=module_name,
                imports=imports,
                exported_symbols=exported_symbols
            )
            
            modules.append(module_info)
        
        # Calculate import counts
        import_counter = Counter()
        for module in modules:
            for imported in module.imports:
                import_counter[imported] += 1
        
        # Update import counts
        for module in modules:
            # Count imports of this module's symbols
            # Simplification: use module name
            module_count = import_counter.get(module.name, 0)
            module.import_count = module_count
        
        return modules
    
    def identify_core_modules(self, threshold: int = 3) -> List[ModuleInfo]:
        """
        Identify core modules (frequently imported).
        
        Args:
            threshold: Minimum import count to be considered core
            
        Returns:
            List of ModuleInfo for core modules
        """
        modules = self._build_module_list()
        
        # Count how many times each module is imported
        import_counter = Counter()
        for module in modules:
            for imported in module.imports:
                import_counter[imported] += 1
        
        # Find core modules
        core_modules = []
        for module in modules:
            count = import_counter.get(module.name.split('.')[-1], 0)
            if count >= threshold:
                module.is_core = True
                module.import_count = count
                core_modules.append(module)
        
        # Sort by import count
        core_modules.sort(key=lambda m: m.import_count, reverse=True)
        
        logger.info(f"Found {len(core_modules)} core modules")
        return core_modules
    
    def find_entry_points(self) -> List[Path]:
        """
        Find entry points (main.py, __main__.py, etc.).
        
        Returns:
            List of entry point file paths
        """
        entry_points = []
        
        # Common entry point patterns
        patterns = [
            'main.py',
            '__main__.py',
            'app.py',
            'server.py',
            'run.py',
        ]
        
        for filepath in self.indexer.index.keys():
            if filepath.name in patterns:
                entry_points.append(filepath)
                logger.debug(f"Found entry point: {filepath}")
        
        # Also check for __main__ blocks
        for filepath, file_index in self.indexer.index.items():
            # Simple heuristic: check if file has if __name__ == "__main__"
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__"' in content:
                        if filepath not in entry_points:
                            entry_points.append(filepath)
            except Exception:
                pass
        
        logger.info(f"Found {len(entry_points)} entry points")
        return entry_points
    
    def detect_test_files(self) -> List[Path]:
        """
        Detect test files.
        
        Returns:
            List of test file paths
        """
        test_files = []
        
        for filepath in self.indexer.index.keys():
            # Check filename patterns
            if (filepath.name.startswith('test_') or 
                filepath.name.endswith('_test.py') or
                'tests' in filepath.parts):
                test_files.append(filepath)
        
        logger.info(f"Found {len(test_files)} test files")
        return test_files
    
    def build_module_graph(self) -> nx.DiGraph:
        """
        Build directed graph of module dependencies.
        
        Returns:
            NetworkX DiGraph where edges represent imports
        """
        graph = nx.DiGraph()
        
        # Add nodes (modules)
        for filepath in self.indexer.index.keys():
            try:
                rel_path = filepath.relative_to(self.root)
                module_name = str(rel_path.with_suffix('')).replace('/', '.')
                graph.add_node(module_name, filepath=filepath)
            except ValueError:
                pass
        
        # Add edges (imports)
        for filepath, file_index in self.indexer.index.items():
            try:
                rel_path = filepath.relative_to(self.root)
                source_module = str(rel_path.with_suffix('')).replace('/', '.')
                
                for imp in file_index.imports:
                    # Only add edges for internal modules
                    target_module = imp.module
                    if target_module in graph:
                        graph.add_edge(source_module, target_module)
            except ValueError:
                pass
        
        logger.info(f"Built dependency graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        return graph
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies (import cycles).
        
        Returns:
            List of cycles, where each cycle is a list of module names
        """
        graph = self.build_module_graph()
        
        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(graph))
            
            if cycles:
                logger.warning(f"Found {len(cycles)} circular dependencies")
                for cycle in cycles:
                    logger.warning(f"  Cycle: {' -> '.join(cycle)}")
            else:
                logger.info("No circular dependencies found")
            
            return cycles
        except Exception as e:
            logger.error(f"Error finding cycles: {e}")
            return []
    
    def get_module_dependencies(self, module_name: str) -> Set[str]:
        """
        Get all dependencies of a module (recursive).
        
        Args:
            module_name: Name of module
            
        Returns:
            Set of all module names this module depends on
        """
        graph = self.build_module_graph()
        
        if module_name not in graph:
            return set()
        
        # Get all descendants (modules this depends on)
        dependencies = set()
        try:
            dependencies = set(nx.descendants(graph, module_name))
        except nx.NetworkXError:
            pass
        
        return dependencies
    
    def get_module_dependents(self, module_name: str) -> Set[str]:
        """
        Get all modules that depend on this module.
        
        Args:
            module_name: Name of module
            
        Returns:
            Set of module names that import this module
        """
        graph = self.build_module_graph()
        
        if module_name not in graph:
            return set()
        
        # Get all ancestors (modules that depend on this)
        dependents = set()
        try:
            dependents = set(nx.ancestors(graph, module_name))
        except nx.NetworkXError:
            pass
        
        return dependents
    
    def find_orphan_modules(self) -> List[ModuleInfo]:
        """
        Find modules that are not imported by any other module.
        
        Returns:
            List of orphan modules
        """
        modules = self._build_module_list()
        
        # Count imports
        import_counter = Counter()
        for module in modules:
            for imported in module.imports:
                import_counter[imported] += 1
        
        # Find orphans
        orphans = []
        for module in modules:
            if import_counter.get(module.name, 0) == 0:
                # Check if it's an entry point
                if module.path not in self.find_entry_points():
                    orphans.append(module)
        
        return orphans


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # First index the codebase
    backend_dir = Path(__file__).parent.parent
    indexer = CodeIndexer(backend_dir)
    
    print("🔍 Indexing codebase...")
    indexer.index_codebase()
    
    # Now scan project structure
    scanner = RepoScanner(indexer)
    
    print("\n🗺️ Scanning project structure...")
    project_map = scanner.scan_project()
    
    print("\n📊 Project Statistics:")
    stats = project_map.stats
    print(f"  Modules: {stats.total_modules}")
    print(f"  Files: {stats.total_files}")
    print(f"  Functions: {stats.total_functions}")
    print(f"  Classes: {stats.total_classes}")
    print(f"  Lines of code: {stats.total_lines}")
    
    print(f"\n🚪 Entry points ({len(stats.entry_points)}):")
    for ep in stats.entry_points:
        print(f"  - {ep.name}")
    
    print(f"\n🔥 Core modules ({len(stats.core_modules)}):")
    for mod in stats.core_modules[:5]:  # Top 5
        print(f"  - {mod}")
    
    if stats.circular_dependencies:
        print(f"\n⚠️ Circular dependencies ({len(stats.circular_dependencies)}):")
        for cycle in stats.circular_dependencies[:3]:  # First 3
            print(f"  - {' -> '.join(cycle)}")
    else:
        print("\n✅ No circular dependencies found")
    
    print("\n✅ Repository Scanner works!")
