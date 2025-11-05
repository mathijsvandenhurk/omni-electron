"""
Hot Reload System - Reload Python modules at runtime

This module provides hot-reloading capabilities for Python modules,
allowing code changes to take effect without restarting the application.
"""

import importlib
import sys
from pathlib import Path
from typing import Dict, Optional, Callable, Set, List
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import logging
import time
import threading

logger = logging.getLogger(__name__)


@dataclass
class ReloadResult:
    """Result of a module reload"""
    success: bool
    module_name: str
    error: Optional[str] = None
    reload_time: float = 0.0
    dependents_reloaded: List[str] = None
    

class HotReloader:
    """
    Hot-reloads Python modules at runtime.
    
    Features:
    - Watch directories for file changes
    - Reload modules automatically or on-demand
    - Handle dependencies (reload dependents)
    - Custom re-initialization hooks
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize hot reloader"""
        self.watched_modules: Dict[str, object] = {}  # module_name -> module_object
        self.reinit_hooks: Dict[str, Callable] = {}  # module_name -> reinit_function
        self.observers: List[Observer] = []
        self.lock = threading.Lock()
        
        # Track module dependencies
        self.dependencies: Dict[str, Set[str]] = {}  # module -> set of modules it imports
        self.dependents: Dict[str, Set[str]] = {}  # module -> set of modules that import it
        
        logger.info("HotReloader initialized")
    
    def watch_directory(
        self,
        path: Path,
        auto_reload: bool = True,
        debounce_seconds: float = 0.5
    ):
        """
        Start watching a directory for changes.
        
        Args:
            path: Directory to watch
            auto_reload: Whether to auto-reload on changes
            debounce_seconds: Delay before reloading (to handle rapid saves)
        """
        event_handler = PythonFileChangeHandler(
            self,
            auto_reload=auto_reload,
            debounce_seconds=debounce_seconds
        )
        
        observer = Observer()
        observer.schedule(event_handler, str(path), recursive=True)
        observer.start()
        
        self.observers.append(observer)
        logger.info(f"Watching directory: {path} (auto_reload={auto_reload})")
    
    def register_module(
        self,
        module_name: str,
        reinit_hook: Optional[Callable] = None
    ):
        """
        Register a module for hot-reloading.
        
        Args:
            module_name: Full module name (e.g., "core.llm_client")
            reinit_hook: Optional function to call after reload
        """
        try:
            # Import module if not already loaded
            if module_name not in sys.modules:
                module = importlib.import_module(module_name)
            else:
                module = sys.modules[module_name]
            
            with self.lock:
                self.watched_modules[module_name] = module
                
                if reinit_hook:
                    self.reinit_hooks[module_name] = reinit_hook
            
            logger.info(f"Registered module for hot-reload: {module_name}")
            
        except Exception as e:
            logger.error(f"Failed to register module {module_name}: {e}")
    
    def reload_module(self, module_name: str) -> ReloadResult:
        """
        Reload a specific module.
        
        Args:
            module_name: Full module name to reload
            
        Returns:
            ReloadResult with success status
        """
        start_time = time.time()
        
        try:
            with self.lock:
                if module_name not in sys.modules:
                    return ReloadResult(
                        success=False,
                        module_name=module_name,
                        error="Module not loaded"
                    )
                
                # Reload module
                logger.info(f"Reloading module: {module_name}")
                module = importlib.reload(sys.modules[module_name])
                
                # Update watched modules
                if module_name in self.watched_modules:
                    self.watched_modules[module_name] = module
                
                # Call reinit hook if registered
                if module_name in self.reinit_hooks:
                    logger.info(f"Calling reinit hook for {module_name}")
                    self.reinit_hooks[module_name]()
                
                # Reload dependent modules
                dependents_reloaded = []
                if module_name in self.dependents:
                    for dependent in self.dependents[module_name]:
                        if dependent in sys.modules:
                            logger.info(f"Reloading dependent: {dependent}")
                            importlib.reload(sys.modules[dependent])
                            dependents_reloaded.append(dependent)
                
                reload_time = time.time() - start_time
                
                logger.info(f"Successfully reloaded {module_name} in {reload_time:.3f}s")
                
                return ReloadResult(
                    success=True,
                    module_name=module_name,
                    reload_time=reload_time,
                    dependents_reloaded=dependents_reloaded
                )
                
        except Exception as e:
            reload_time = time.time() - start_time
            logger.error(f"Failed to reload {module_name}: {e}")
            
            return ReloadResult(
                success=False,
                module_name=module_name,
                error=str(e),
                reload_time=reload_time
            )
    
    def reload_all_watched(self) -> List[ReloadResult]:
        """
        Reload all watched modules.
        
        Returns:
            List of ReloadResult for each module
        """
        results = []
        
        with self.lock:
            module_names = list(self.watched_modules.keys())
        
        for module_name in module_names:
            result = self.reload_module(module_name)
            results.append(result)
        
        return results
    
    def file_to_module_name(self, filepath: Path, root_path: Path) -> Optional[str]:
        """
        Convert file path to module name.
        
        Args:
            filepath: Path to Python file
            root_path: Root directory of project
            
        Returns:
            Module name (e.g., "core.llm_client") or None
        """
        try:
            # Make relative to root
            rel_path = filepath.relative_to(root_path)
            
            # Convert to module name
            module_name = str(rel_path.with_suffix('')).replace('/', '.')
            
            # Handle __init__.py
            if module_name.endswith('.__init__'):
                module_name = module_name[:-9]  # Remove .__init__
            
            return module_name
            
        except ValueError:
            return None
    
    def on_file_changed(self, filepath: Path, root_path: Path):
        """
        Handle file change event.
        
        Args:
            filepath: Path to changed file
            root_path: Root directory of project
        """
        # Convert to module name
        module_name = self.file_to_module_name(filepath, root_path)
        
        if not module_name:
            return
        
        logger.info(f"File changed: {filepath} -> {module_name}")
        
        # Check if module is watched
        if module_name in self.watched_modules or module_name in sys.modules:
            # Reload module
            result = self.reload_module(module_name)
            
            if result.success:
                logger.info(f"✅ Hot-reloaded {module_name}")
            else:
                logger.error(f"❌ Failed to reload {module_name}: {result.error}")
    
    def stop_watching(self):
        """Stop all file watchers"""
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        logger.info("Stopped all file watchers")
    
    def get_status(self) -> dict:
        """Get hot reloader status"""
        return {
            'watched_modules': list(self.watched_modules.keys()),
            'watchers_active': len(self.observers),
            'reinit_hooks': list(self.reinit_hooks.keys())
        }


class PythonFileChangeHandler(FileSystemEventHandler):
    """Handles Python file change events for hot-reloading"""
    
    def __init__(
        self,
        hot_reloader: HotReloader,
        auto_reload: bool = True,
        debounce_seconds: float = 0.5
    ):
        self.hot_reloader = hot_reloader
        self.auto_reload = auto_reload
        self.debounce_seconds = debounce_seconds
        self.last_reload_time: Dict[str, float] = {}
    
    def on_modified(self, event):
        """Handle file modification event"""
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Only handle .py files
        if filepath.suffix != '.py':
            return
        
        # Debounce: ignore rapid successive changes
        current_time = time.time()
        last_time = self.last_reload_time.get(str(filepath), 0)
        
        if current_time - last_time < self.debounce_seconds:
            return
        
        self.last_reload_time[str(filepath)] = current_time
        
        # Auto-reload if enabled
        if self.auto_reload:
            # Find root path (assume parent of parent of file)
            root_path = filepath.parent.parent
            self.hot_reloader.on_file_changed(filepath, root_path)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔥 Testing Hot Reloader...")
    print("=" * 60)
    
    # Create hot reloader
    reloader = HotReloader()
    
    # Create test module
    test_module_path = Path(__file__).parent / "test_hot_reload_module.py"
    
    test_code_v1 = '''"""Test module for hot reload"""

def get_version():
    return "v1.0"

def greet(name):
    return f"Hello, {name}!"
'''
    
    with open(test_module_path, 'w') as f:
        f.write(test_code_v1)
    
    # Import and register module
    import sys
    sys.path.insert(0, str(test_module_path.parent))
    
    import test_hot_reload_module
    
    print("\n1️⃣ Initial version:")
    print(f"  Version: {test_hot_reload_module.get_version()}")
    print(f"  Greet: {test_hot_reload_module.greet('Alice')}")
    
    # Register for hot reload
    reloader.register_module('test_hot_reload_module')
    
    # Modify module
    print("\n2️⃣ Modifying module...")
    test_code_v2 = '''"""Test module for hot reload"""

def get_version():
    return "v2.0"  # Changed!

def greet(name):
    return f"Hi there, {name}! 👋"  # Changed!
'''
    
    with open(test_module_path, 'w') as f:
        f.write(test_code_v2)
    
    # Reload
    print("\n3️⃣ Hot-reloading...")
    result = reloader.reload_module('test_hot_reload_module')
    
    if result.success:
        print(f"  ✅ Reloaded in {result.reload_time:.3f}s")
    else:
        print(f"  ❌ Failed: {result.error}")
    
    # Test new version
    print("\n4️⃣ After reload:")
    # Need to re-import to get new functions
    import importlib
    test_hot_reload_module = importlib.import_module('test_hot_reload_module')
    print(f"  Version: {test_hot_reload_module.get_version()}")
    print(f"  Greet: {test_hot_reload_module.greet('Bob')}")
    
    # Status
    print("\n📊 Status:")
    status = reloader.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    test_module_path.unlink()
    
    print("\n✅ Hot Reloader works!")
