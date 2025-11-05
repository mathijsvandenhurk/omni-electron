"""
AST Analyzer - Analyzes Python code using Abstract Syntax Trees

This module provides tools to parse, analyze, and understand Python code
structure using the built-in ast module.
"""

import ast
import inspect
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class FunctionSignature:
    """Represents a function signature"""
    name: str
    parameters: List[str]
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    
    
@dataclass
class FunctionInfo:
    """Information about a function definition"""
    name: str
    lineno: int
    end_lineno: int
    signature: FunctionSignature
    docstring: Optional[str] = None
    complexity: int = 1  # Cyclomatic complexity
    calls: List[str] = field(default_factory=list)  # Functions this calls
    source_code: Optional[str] = None
    

@dataclass
class ClassInfo:
    """Information about a class definition"""
    name: str
    lineno: int
    end_lineno: int
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    

@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    names: List[str]  # What's imported (empty for `import module`)
    alias: Optional[str] = None
    lineno: int = 0
    is_from_import: bool = False


class ASTAnalyzer:
    """
    Analyzes Python code using Abstract Syntax Trees.
    
    Provides methods to:
    - Parse Python files into AST
    - Extract functions, classes, imports
    - Analyze function signatures and calls
    - Calculate code metrics
    """
    
    def __init__(self):
        self.current_file: Optional[Path] = None
        self.current_source: Optional[str] = None
        self.current_tree: Optional[ast.Module] = None
        
    def parse_file(self, filepath: Path) -> Optional[ast.Module]:
        """
        Parse a Python file into an AST.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            ast.Module if successful, None if parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(filepath))
            
            self.current_file = filepath
            self.current_source = source
            self.current_tree = tree
            
            logger.info(f"Successfully parsed {filepath}")
            return tree
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            return None
    
    def parse_source(self, source: str, filename: str = "<string>") -> Optional[ast.Module]:
        """
        Parse Python source code into an AST.
        
        Args:
            source: Python source code
            filename: Optional filename for error messages
            
        Returns:
            ast.Module if successful, None if parsing fails
        """
        try:
            tree = ast.parse(source, filename=filename)
            self.current_source = source
            self.current_tree = tree
            return tree
        except SyntaxError as e:
            logger.error(f"Syntax error in {filename}: {e}")
            return None
            
    def get_source_segment(self, node: ast.AST) -> Optional[str]:
        """Get the source code for a specific AST node"""
        if not self.current_source:
            return None
            
        try:
            return ast.get_source_segment(self.current_source, node)
        except Exception:
            return None
    
    def find_functions(self, tree: Optional[ast.Module] = None) -> List[FunctionInfo]:
        """
        Extract all function definitions from an AST.
        
        Args:
            tree: AST module to analyze (uses current_tree if None)
            
        Returns:
            List of FunctionInfo objects
        """
        if tree is None:
            tree = self.current_tree
            
        if tree is None:
            logger.warning("No AST tree available")
            return []
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._analyze_function(node)
                functions.append(func_info)
        
        return functions
    
    def find_classes(self, tree: Optional[ast.Module] = None) -> List[ClassInfo]:
        """
        Extract all class definitions from an AST.
        
        Args:
            tree: AST module to analyze (uses current_tree if None)
            
        Returns:
            List of ClassInfo objects
        """
        if tree is None:
            tree = self.current_tree
            
        if tree is None:
            logger.warning("No AST tree available")
            return []
        
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)
        
        return classes
    
    def extract_imports(self, tree: Optional[ast.Module] = None) -> List[ImportInfo]:
        """
        Extract all import statements from an AST.
        
        Args:
            tree: AST module to analyze (uses current_tree if None)
            
        Returns:
            List of ImportInfo objects
        """
        if tree is None:
            tree = self.current_tree
            
        if tree is None:
            logger.warning("No AST tree available")
            return []
        
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        lineno=node.lineno,
                        is_from_import=False
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Skip relative imports without module
                    names = [alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        module=node.module,
                        names=names,
                        lineno=node.lineno,
                        is_from_import=True
                    ))
        
        return imports
    
    def find_function_calls(self, node: ast.AST, target: Optional[str] = None) -> List[str]:
        """
        Find all function calls in an AST node.
        
        Args:
            node: AST node to search
            target: If provided, only return calls to this function
            
        Returns:
            List of function names called
        """
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Get function name
                func_name = self._get_call_name(child.func)
                if func_name:
                    if target is None or func_name == target:
                        calls.append(func_name)
        
        return calls
    
    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        """Analyze a function definition node"""
        
        # Extract signature
        signature = FunctionSignature(
            name=node.name,
            parameters=[arg.arg for arg in node.args.args],
            return_type=self._get_annotation(node.returns),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            is_async=isinstance(node, ast.AsyncFunctionDef)
        )
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Find function calls
        calls = self.find_function_calls(node)
        
        # Calculate cyclomatic complexity (simplified)
        complexity = self._calculate_complexity(node)
        
        # Get source code
        source_code = self.get_source_segment(node)
        
        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            signature=signature,
            docstring=docstring,
            complexity=complexity,
            calls=calls,
            source_code=source_code
        )
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition node"""
        
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}")  # type: ignore
        
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._analyze_function(item)
                func_info.signature.is_method = True
                methods.append(func_info)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            bases=bases,
            methods=methods,
            docstring=docstring,
            decorators=decorators
        )
    
    def _get_annotation(self, annotation: Optional[ast.expr]) -> Optional[str]:
        """Extract type annotation as string"""
        if annotation is None:
            return None
        
        try:
            return ast.unparse(annotation)
        except Exception:
            return None
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return "unknown"
    
    def _get_call_name(self, node: ast.expr) -> Optional[str]:
        """Extract function name from Call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # For method calls like obj.method(), return just "method"
            return node.attr
        return None
    
    def _calculate_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """
        Calculate cyclomatic complexity (simplified).
        
        Counts decision points: if, for, while, except, with, and, or
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each 'and' or 'or' adds complexity
                complexity += len(child.values) - 1
        
        return complexity
    
    def get_function_by_name(self, name: str, tree: Optional[ast.Module] = None) -> Optional[FunctionInfo]:
        """Find a specific function by name"""
        functions = self.find_functions(tree)
        for func in functions:
            if func.name == name:
                return func
        return None
    
    def get_class_by_name(self, name: str, tree: Optional[ast.Module] = None) -> Optional[ClassInfo]:
        """Find a specific class by name"""
        classes = self.find_classes(tree)
        for cls in classes:
            if cls.name == name:
                return cls
        return None
    
    def analyze_file_summary(self, filepath: Path) -> Dict[str, Any]:
        """
        Analyze a file and return a summary.
        
        Returns:
            Dictionary with counts and statistics
        """
        tree = self.parse_file(filepath)
        if tree is None:
            return {"error": "Failed to parse file"}
        
        functions = self.find_functions(tree)
        classes = self.find_classes(tree)
        imports = self.extract_imports(tree)
        
        # Calculate total lines of code
        if self.current_source:
            total_lines = len(self.current_source.splitlines())
        else:
            total_lines = 0
        
        # Calculate average complexity
        if functions:
            avg_complexity = sum(f.complexity for f in functions) / len(functions)
        else:
            avg_complexity = 0
        
        return {
            "filepath": str(filepath),
            "total_lines": total_lines,
            "function_count": len(functions),
            "class_count": len(classes),
            "import_count": len(imports),
            "avg_complexity": round(avg_complexity, 2),
            "functions": [f.name for f in functions],
            "classes": [c.name for c in classes],
            "imports": [i.module for i in imports]
        }


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test by analyzing this file
    analyzer = ASTAnalyzer()
    current_file = Path(__file__)
    
    print(f"Analyzing {current_file.name}...")
    print("=" * 60)
    
    summary = analyzer.analyze_file_summary(current_file)
    
    print(f"Total lines: {summary['total_lines']}")
    print(f"Functions: {summary['function_count']}")
    print(f"Classes: {summary['class_count']}")
    print(f"Imports: {summary['import_count']}")
    print(f"Avg complexity: {summary['avg_complexity']}")
    
    print("\nFunctions found:")
    for func_name in summary['functions']:
        print(f"  - {func_name}")
    
    print("\nClasses found:")
    for class_name in summary['classes']:
        print(f"  - {class_name}")
