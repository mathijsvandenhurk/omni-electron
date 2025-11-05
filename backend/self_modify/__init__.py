"""
Self-Modification Engine

Components for analyzing, modifying, and hot-reloading Omni's own code.
"""

from .ast_analyzer import ASTAnalyzer, FunctionInfo, ClassInfo
from .code_indexer import CodeIndexer, FileIndex

__all__ = [
    'ASTAnalyzer',
    'FunctionInfo',
    'ClassInfo',
    'CodeIndexer',
    'FileIndex',
]

# These will be added as we implement them:
# from .repo_scanner import RepoScanner, ProjectMap
