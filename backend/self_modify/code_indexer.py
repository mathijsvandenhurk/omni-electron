"""
Code Indexer - Maintains searchable index of codebase

This module indexes all Python files in a project and provides
fast search capabilities for symbols, patterns, and code structure.
"""

import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .ast_analyzer import ASTAnalyzer, FunctionInfo, ClassInfo, ImportInfo

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Represents a location in source code"""
    filepath: Path
    lineno: int
    end_lineno: int
    column: int = 0
    

@dataclass
class FileStats:
    """Statistics about a file"""
    filepath: Path
    lines_of_code: int
    function_count: int
    class_count: int
    import_count: int
    avg_complexity: float
    last_modified: float
    

@dataclass
class FileIndex:
    """Complete index of a single file"""
    filepath: Path
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    last_modified: float
    hash: str  # For change detection
    stats: FileStats
    

@dataclass
class Match:
    """Represents a search match"""
    filepath: Path
    lineno: int
    column: int
    matched_text: str
    context: str  # Surrounding lines


class CodeIndexer:
    """
    Maintains a searchable index of the entire codebase.
    
    Features:
    - Fast symbol lookups (functions, classes, variables)
    - Pattern searching (regex support)
    - Incremental updates via file watching
    - Change detection via file hashing
    """
    
    def __init__(self, root_dir: Path):
        """
        Initialize code indexer.
        
        Args:
            root_dir: Root directory to index
        """
        self.root = Path(root_dir)
        self.index: Dict[Path, FileIndex] = {}
        self.analyzer = ASTAnalyzer()
        
        # Symbol maps for fast lookup
        self.function_map: Dict[str, List[Location]] = {}
        self.class_map: Dict[str, List[Location]] = {}
        
        logger.info(f"CodeIndexer initialized for {root_dir}")
    
    def index_codebase(
        self,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[Path, FileIndex]:
        """
        Index all Python files in the codebase.
        
        Args:
            exclude_patterns: Glob patterns to exclude (e.g., ['**/tests/**', '**/__pycache__/**'])
            
        Returns:
            Dictionary mapping file paths to FileIndex objects
        """
        if exclude_patterns is None:
            exclude_patterns = [
                '**/__pycache__/**',
                '**/venv/**',
                '**/.venv/**',
                '**/node_modules/**',
                '**/.git/**',
                '**/dist/**',
                '**/build/**',
            ]
        
        logger.info(f"Starting full codebase index from {self.root}")
        
        # Find all Python files
        python_files = list(self.root.rglob('*.py'))
        
        # Filter out excluded patterns
        filtered_files = []
        for filepath in python_files:
            rel_path = filepath.relative_to(self.root)
            excluded = False
            for pattern in exclude_patterns:
                if rel_path.match(pattern):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(filepath)
        
        logger.info(f"Found {len(filtered_files)} Python files to index")
        
        # Index each file
        for filepath in filtered_files:
            try:
                self._index_file(filepath)
            except Exception as e:
                logger.error(f"Failed to index {filepath}: {e}")
        
        logger.info(f"Indexing complete: {len(self.index)} files indexed")
        
        return self.index
    
    def _index_file(self, filepath: Path) -> Optional[FileIndex]:
        """Index a single file"""
        try:
            # Get file metadata
            stat = filepath.stat()
            last_modified = stat.st_mtime
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(filepath)
            
            # Check if file changed (if already indexed)
            if filepath in self.index:
                old_index = self.index[filepath]
                if old_index.hash == file_hash:
                    logger.debug(f"File unchanged, skipping: {filepath}")
                    return old_index
            
            # Parse file
            tree = self.analyzer.parse_file(filepath)
            if tree is None:
                logger.warning(f"Could not parse {filepath}")
                return None
            
            # Extract information
            functions = self.analyzer.find_functions(tree)
            classes = self.analyzer.find_classes(tree)
            imports = self.analyzer.extract_imports(tree)
            
            # Calculate statistics
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            avg_complexity = sum(f.complexity for f in functions) / len(functions) if functions else 0
            
            stats = FileStats(
                filepath=filepath,
                lines_of_code=loc,
                function_count=len(functions),
                class_count=len(classes),
                import_count=len(imports),
                avg_complexity=round(avg_complexity, 2),
                last_modified=last_modified
            )
            
            # Create file index
            file_index = FileIndex(
                filepath=filepath,
                functions=functions,
                classes=classes,
                imports=imports,
                last_modified=last_modified,
                hash=file_hash,
                stats=stats
            )
            
            # Update main index
            self.index[filepath] = file_index
            
            # Update symbol maps
            self._update_symbol_maps(filepath, functions, classes)
            
            logger.debug(f"Indexed {filepath}: {len(functions)} funcs, {len(classes)} classes")
            
            return file_index
            
        except Exception as e:
            logger.error(f"Error indexing {filepath}: {e}")
            return None
    
    def _update_symbol_maps(
        self,
        filepath: Path,
        functions: List[FunctionInfo],
        classes: List[ClassInfo]
    ):
        """Update symbol maps for fast lookup"""
        
        # Clear old entries for this file
        for func_name in list(self.function_map.keys()):
            self.function_map[func_name] = [
                loc for loc in self.function_map[func_name]
                if loc.filepath != filepath
            ]
            if not self.function_map[func_name]:
                del self.function_map[func_name]
        
        for class_name in list(self.class_map.keys()):
            self.class_map[class_name] = [
                loc for loc in self.class_map[class_name]
                if loc.filepath != filepath
            ]
            if not self.class_map[class_name]:
                del self.class_map[class_name]
        
        # Add new entries
        for func in functions:
            if func.name not in self.function_map:
                self.function_map[func.name] = []
            self.function_map[func.name].append(Location(
                filepath=filepath,
                lineno=func.lineno,
                end_lineno=func.end_lineno
            ))
        
        for cls in classes:
            if cls.name not in self.class_map:
                self.class_map[cls.name] = []
            self.class_map[cls.name].append(Location(
                filepath=filepath,
                lineno=cls.lineno,
                end_lineno=cls.end_lineno
            ))
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file contents"""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def find_definition(self, symbol: str) -> Optional[Location]:
        """
        Find where a symbol (function or class) is defined.
        
        Args:
            symbol: Name of function or class
            
        Returns:
            Location of definition, or None if not found
        """
        # Check functions
        if symbol in self.function_map:
            # Return first match (could have duplicates)
            return self.function_map[symbol][0]
        
        # Check classes
        if symbol in self.class_map:
            return self.class_map[symbol][0]
        
        return None
    
    def find_references(self, symbol: str) -> List[Location]:
        """
        Find all references to a symbol.
        
        Args:
            symbol: Name of function or class
            
        Returns:
            List of locations where symbol is referenced
        """
        references = []
        
        # Search through all indexed files
        for filepath, file_index in self.index.items():
            # Check function calls
            for func in file_index.functions:
                if symbol in func.calls:
                    references.append(Location(
                        filepath=filepath,
                        lineno=func.lineno,
                        end_lineno=func.end_lineno
                    ))
        
        return references
    
    def search_pattern(
        self,
        pattern: str,
        use_regex: bool = False,
        case_sensitive: bool = False
    ) -> List[Match]:
        """
        Search for a pattern in all indexed files.
        
        Args:
            pattern: Text or regex pattern to search for
            use_regex: Whether to treat pattern as regex
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of matches with context
        """
        matches = []
        
        # Compile regex if needed
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return []
        else:
            # Escape special regex chars for literal search
            pattern = re.escape(pattern)
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        
        # Search through all files
        for filepath in self.index.keys():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for lineno, line in enumerate(lines, start=1):
                    match_obj = regex.search(line)
                    if match_obj:
                        # Get context (line before and after)
                        context_start = max(0, lineno - 2)
                        context_end = min(len(lines), lineno + 1)
                        context = ''.join(lines[context_start:context_end])
                        
                        matches.append(Match(
                            filepath=filepath,
                            lineno=lineno,
                            column=match_obj.start(),
                            matched_text=match_obj.group(0),
                            context=context
                        ))
            except Exception as e:
                logger.error(f"Error searching {filepath}: {e}")
        
        return matches
    
    def get_file_stats(self, filepath: Path) -> Optional[FileStats]:
        """Get statistics for a file"""
        if filepath in self.index:
            return self.index[filepath].stats
        return None
    
    def get_project_stats(self) -> Dict[str, any]:
        """Get overall project statistics"""
        total_files = len(self.index)
        total_functions = sum(len(idx.functions) for idx in self.index.values())
        total_classes = sum(len(idx.classes) for idx in self.index.values())
        total_loc = sum(idx.stats.lines_of_code for idx in self.index.values())
        
        # Average complexity across all functions
        all_complexities = [
            func.complexity
            for idx in self.index.values()
            for func in idx.functions
        ]
        avg_complexity = sum(all_complexities) / len(all_complexities) if all_complexities else 0
        
        return {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_lines_of_code': total_loc,
            'average_complexity': round(avg_complexity, 2),
            'most_complex_functions': self._get_most_complex_functions(5)
        }
    
    def _get_most_complex_functions(self, n: int = 5) -> List[Dict]:
        """Get N most complex functions"""
        all_functions = []
        for filepath, idx in self.index.items():
            for func in idx.functions:
                all_functions.append({
                    'name': func.name,
                    'filepath': str(filepath),
                    'complexity': func.complexity,
                    'lineno': func.lineno
                })
        
        # Sort by complexity
        all_functions.sort(key=lambda f: f['complexity'], reverse=True)
        
        return all_functions[:n]
    
    def refresh_file(self, filepath: Path) -> Optional[FileIndex]:
        """
        Re-index a specific file (e.g., after modification).
        
        Args:
            filepath: Path to file to refresh
            
        Returns:
            Updated FileIndex, or None if failed
        """
        logger.info(f"Refreshing index for {filepath}")
        return self._index_file(filepath)
    
    def list_all_functions(self) -> List[str]:
        """Get list of all function names in codebase"""
        return sorted(self.function_map.keys())
    
    def list_all_classes(self) -> List[str]:
        """Get list of all class names in codebase"""
        return sorted(self.class_map.keys())


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Index the backend directory
    backend_dir = Path(__file__).parent.parent
    indexer = CodeIndexer(backend_dir)
    
    print("🔍 Indexing codebase...")
    indexer.index_codebase()
    
    print("\n📊 Project Statistics:")
    stats = indexer.get_project_stats()
    print(f"  Files: {stats['total_files']}")
    print(f"  Functions: {stats['total_functions']}")
    print(f"  Classes: {stats['total_classes']}")
    print(f"  Lines of code: {stats['total_lines_of_code']}")
    print(f"  Avg complexity: {stats['average_complexity']}")
    
    print("\n🔥 Most complex functions:")
    for func in stats['most_complex_functions']:
        print(f"  - {func['name']} (complexity: {func['complexity']}) in {func['filepath']}")
    
    print("\n🔍 Finding definition of 'parse_file':")
    loc = indexer.find_definition("parse_file")
    if loc:
        print(f"  Found at {loc.filepath}:{loc.lineno}")
    
    print("\n✅ Code Indexer works!")
