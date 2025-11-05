"""
Safe Code Rewriter - Safely modifies Python code using libcst

This module provides tools to modify Python code while preserving
formatting, comments, and code structure. Uses libcst (concrete syntax tree)
instead of ast to maintain all whitespace and comments.
"""

import libcst as cst
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import logging
import difflib

logger = logging.getLogger(__name__)


@dataclass
class ChangeResult:
    """Result of a code modification"""
    success: bool
    filepath: Path
    diff: str
    error: Optional[str] = None
    backup_created: bool = False
    

class SafeCodeRewriter:
    """
    Safely modifies Python code using libcst.
    
    Features:
    - Preserves formatting and comments
    - Syntax validation before writing
    - Automatic backups
    - Diff generation
    - Rollback capability
    """
    
    def __init__(self, create_backups: bool = True):
        """
        Initialize code rewriter.
        
        Args:
            create_backups: Whether to create .bak files before modifying
        """
        self.create_backups = create_backups
        logger.info("SafeCodeRewriter initialized")
    
    def modify_function(
        self,
        filepath: Path,
        func_name: str,
        new_body: str
    ) -> ChangeResult:
        """
        Replace the body of a function.
        
        Args:
            filepath: Path to Python file
            func_name: Name of function to modify
            new_body: New function body (as string)
            
        Returns:
            ChangeResult with success status and diff
        """
        try:
            # Read original file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Parse with libcst
            tree = cst.parse_module(original_code)
            
            # Create transformer to modify function
            transformer = FunctionBodyTransformer(func_name, new_body)
            modified_tree = tree.visit(transformer)
            
            if not transformer.found:
                return ChangeResult(
                    success=False,
                    filepath=filepath,
                    diff="",
                    error=f"Function '{func_name}' not found"
                )
            
            # Generate new code
            new_code = modified_tree.code
            
            # Validate syntax
            try:
                compile(new_code, str(filepath), 'exec')
            except SyntaxError as e:
                return ChangeResult(
                    success=False,
                    filepath=filepath,
                    diff="",
                    error=f"Generated code has syntax error: {e}"
                )
            
            # Create backup if enabled
            backup_created = False
            if self.create_backups:
                backup_path = filepath.with_suffix('.py.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_code)
                backup_created = True
                logger.info(f"Created backup: {backup_path}")
            
            # Write modified code
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            # Generate diff
            diff = self._generate_diff(original_code, new_code, filepath)
            
            logger.info(f"Successfully modified function '{func_name}' in {filepath}")
            
            return ChangeResult(
                success=True,
                filepath=filepath,
                diff=diff,
                backup_created=backup_created
            )
            
        except Exception as e:
            logger.error(f"Error modifying function: {e}")
            return ChangeResult(
                success=False,
                filepath=filepath,
                diff="",
                error=str(e)
            )
    
    def add_import(
        self,
        filepath: Path,
        import_stmt: str,
        from_module: Optional[str] = None
    ) -> ChangeResult:
        """
        Add an import statement to a file.
        
        Args:
            filepath: Path to Python file
            import_stmt: What to import (e.g., "functools")
            from_module: If provided, creates "from X import Y" statement
            
        Returns:
            ChangeResult with success status
        """
        try:
            # Read original file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Parse with libcst
            tree = cst.parse_module(original_code)
            
            # Create import statement
            if from_module:
                # from module import something
                new_import = cst.SimpleStatementLine([
                    cst.ImportFrom(
                        module=cst.Attribute(value=cst.Name(from_module.split('.')[0]), attr=cst.Name(from_module.split('.')[-1])) if '.' in from_module else cst.Name(from_module),
                        names=[cst.ImportAlias(name=cst.Name(import_stmt))]
                    )
                ])
            else:
                # import module
                new_import = cst.SimpleStatementLine([
                    cst.Import(names=[cst.ImportAlias(name=cst.Name(import_stmt))])
                ])
            
            # Add import at the top (after docstring if present)
            transformer = ImportAdder(new_import)
            modified_tree = tree.visit(transformer)
            
            # Generate new code
            new_code = modified_tree.code
            
            # Validate syntax
            compile(new_code, str(filepath), 'exec')
            
            # Create backup
            if self.create_backups:
                backup_path = filepath.with_suffix('.py.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_code)
            
            # Write modified code
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            # Generate diff
            diff = self._generate_diff(original_code, new_code, filepath)
            
            logger.info(f"Added import '{import_stmt}' to {filepath}")
            
            return ChangeResult(
                success=True,
                filepath=filepath,
                diff=diff,
                backup_created=self.create_backups
            )
            
        except Exception as e:
            logger.error(f"Error adding import: {e}")
            return ChangeResult(
                success=False,
                filepath=filepath,
                diff="",
                error=str(e)
            )
    
    def add_decorator(
        self,
        filepath: Path,
        func_name: str,
        decorator: str
    ) -> ChangeResult:
        """
        Add a decorator to a function.
        
        Args:
            filepath: Path to Python file
            func_name: Name of function
            decorator: Decorator to add (e.g., "@lru_cache")
            
        Returns:
            ChangeResult with success status
        """
        try:
            # Read original file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Parse with libcst
            tree = cst.parse_module(original_code)
            
            # Remove @ if present
            if decorator.startswith('@'):
                decorator = decorator[1:]
            
            # Create transformer to add decorator
            transformer = DecoratorAdder(func_name, decorator)
            modified_tree = tree.visit(transformer)
            
            if not transformer.found:
                return ChangeResult(
                    success=False,
                    filepath=filepath,
                    diff="",
                    error=f"Function '{func_name}' not found"
                )
            
            # Generate new code
            new_code = modified_tree.code
            
            # Validate syntax
            compile(new_code, str(filepath), 'exec')
            
            # Create backup
            if self.create_backups:
                backup_path = filepath.with_suffix('.py.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_code)
            
            # Write modified code
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            # Generate diff
            diff = self._generate_diff(original_code, new_code, filepath)
            
            logger.info(f"Added decorator '{decorator}' to '{func_name}' in {filepath}")
            
            return ChangeResult(
                success=True,
                filepath=filepath,
                diff=diff,
                backup_created=self.create_backups
            )
            
        except Exception as e:
            logger.error(f"Error adding decorator: {e}")
            return ChangeResult(
                success=False,
                filepath=filepath,
                diff="",
                error=str(e)
            )
    
    def _generate_diff(self, old_code: str, new_code: str, filepath: Path) -> str:
        """Generate unified diff between old and new code"""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{filepath} (original)",
            tofile=f"{filepath} (modified)",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def restore_backup(self, filepath: Path) -> bool:
        """
        Restore file from backup.
        
        Args:
            filepath: Path to file to restore
            
        Returns:
            True if successful
        """
        backup_path = filepath.with_suffix('.py.bak')
        
        if not backup_path.exists():
            logger.error(f"No backup found for {filepath}")
            return False
        
        try:
            # Read backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_code = f.read()
            
            # Restore
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(backup_code)
            
            logger.info(f"Restored {filepath} from backup")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False


class FunctionBodyTransformer(cst.CSTTransformer):
    """Transformer to replace function body"""
    
    def __init__(self, target_func: str, new_body: str):
        self.target_func = target_func
        self.new_body = new_body
        self.found = False
    
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Replace function body if it matches target"""
        if updated_node.name.value == self.target_func:
            self.found = True
            
            # Parse new body
            new_body_module = cst.parse_module(self.new_body)
            new_body_stmts = new_body_module.body
            
            # Replace body
            return updated_node.with_changes(body=cst.IndentedBlock(body=new_body_stmts))
        
        return updated_node


class DecoratorAdder(cst.CSTTransformer):
    """Transformer to add decorator to function"""
    
    def __init__(self, target_func: str, decorator: str):
        self.target_func = target_func
        self.decorator = decorator
        self.found = False
    
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add decorator if function matches target"""
        if updated_node.name.value == self.target_func:
            self.found = True
            
            # Create new decorator
            new_decorator = cst.Decorator(decorator=cst.Name(self.decorator))
            
            # Add to existing decorators
            new_decorators = list(updated_node.decorators) + [new_decorator]
            
            return updated_node.with_changes(decorators=new_decorators)
        
        return updated_node


class ImportAdder(cst.CSTTransformer):
    """Transformer to add import statement"""
    
    def __init__(self, import_stmt: cst.SimpleStatementLine):
        self.import_stmt = import_stmt
        self.added = False
    
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module
    ) -> cst.Module:
        """Add import at top of module"""
        if self.added:
            return updated_node
        
        # Find where to insert (after docstring if present)
        insert_index = 0
        if (updated_node.body and 
            isinstance(updated_node.body[0], cst.SimpleStatementLine) and
            isinstance(updated_node.body[0].body[0], cst.Expr) and
            isinstance(updated_node.body[0].body[0].value, cst.SimpleString)):
            # Has docstring
            insert_index = 1
        
        # Insert import
        new_body = list(updated_node.body)
        new_body.insert(insert_index, self.import_stmt)
        
        self.added = True
        return updated_node.with_changes(body=new_body)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create a test file
    test_file = Path(__file__).parent / "test_rewriter_target.py"
    
    test_code = '''"""Test file for code rewriter"""

def greet(name):
    """Say hello"""
    return f"Hello, {name}!"

def calculate(x, y):
    """Add two numbers"""
    return x + y
'''
    
    # Write test file
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print("🔧 Testing Safe Code Rewriter...")
    print("=" * 60)
    
    rewriter = SafeCodeRewriter()
    
    # Test 1: Add decorator
    print("\n1️⃣ Adding decorator to 'calculate'...")
    result = rewriter.add_decorator(test_file, "calculate", "@lru_cache")
    
    if result.success:
        print(f"✅ Success! Backup: {result.backup_created}")
        print("\nDiff:")
        print(result.diff)
    else:
        print(f"❌ Failed: {result.error}")
    
    # Test 2: Add import
    print("\n2️⃣ Adding import...")
    result = rewriter.add_import(test_file, "lru_cache", "functools")
    
    if result.success:
        print(f"✅ Success!")
        print("\nDiff:")
        print(result.diff[:200])  # First 200 chars
    else:
        print(f"❌ Failed: {result.error}")
    
    # Show final result
    print("\n📄 Modified file:")
    with open(test_file, 'r') as f:
        print(f.read())
    
    # Cleanup
    test_file.unlink()
    backup_file = test_file.with_suffix('.py.bak')
    if backup_file.exists():
        backup_file.unlink()
    
    print("\n✅ Code Rewriter works!")
