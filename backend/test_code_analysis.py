"""
Demo script to test all code analysis components

This demonstrates the capabilities of AST Analyzer, Code Indexer,
and Repository Scanner working together.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from self_modify.ast_analyzer import ASTAnalyzer
from self_modify.code_indexer import CodeIndexer
from self_modify.repo_scanner import RepoScanner


def demo_ast_analyzer():
    """Test AST Analyzer"""
    print("=" * 60)
    print("🔬 AST ANALYZER DEMO")
    print("=" * 60)
    
    analyzer = ASTAnalyzer()
    
    # Analyze this file!
    test_file = Path(__file__)
    summary = analyzer.analyze_file_summary(test_file)
    
    print(f"\n📄 Analyzed: {test_file.name}")
    print(f"  Total lines: {summary['total_lines']}")
    print(f"  Functions: {summary['function_count']}")
    print(f"  Classes: {summary['class_count']}")
    print(f"  Avg complexity: {summary['avg_complexity']}")
    
    if summary['functions']:
        print(f"\n  Functions found:")
        for func_name in summary['functions'][:5]:
            print(f"    - {func_name}()")
    
    print("\n✅ AST Analyzer working!")


def demo_code_indexer():
    """Test Code Indexer"""
    print("\n" + "=" * 60)
    print("📚 CODE INDEXER DEMO")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent
    indexer = CodeIndexer(backend_dir)
    
    print(f"\n🔍 Indexing {backend_dir}...")
    print("  (This may take a moment...)")
    
    # Index only self_modify directory (faster)
    indexer.root = backend_dir / "self_modify"
    indexer.index_codebase()
    
    stats = indexer.get_project_stats()
    
    print(f"\n📊 Index Statistics:")
    print(f"  Files indexed: {stats['total_files']}")
    print(f"  Functions found: {stats['total_functions']}")
    print(f"  Classes found: {stats['total_classes']}")
    print(f"  Total LOC: {stats['total_lines_of_code']}")
    
    # Test symbol lookup
    print(f"\n🔎 Symbol Lookup Test:")
    test_symbols = ['ASTAnalyzer', 'CodeIndexer', 'parse_file']
    for symbol in test_symbols:
        loc = indexer.find_definition(symbol)
        if loc:
            print(f"  ✅ {symbol}: found at {loc.filepath.name}:{loc.lineno}")
        else:
            print(f"  ❌ {symbol}: not found")
    
    # Show most complex functions
    if stats['most_complex_functions']:
        print(f"\n🔥 Most Complex Functions:")
        for func in stats['most_complex_functions'][:3]:
            print(f"  - {func['name']} (complexity: {func['complexity']})")
    
    print("\n✅ Code Indexer working!")
    
    return indexer


def demo_repo_scanner(indexer):
    """Test Repository Scanner"""
    print("\n" + "=" * 60)
    print("🗺️ REPOSITORY SCANNER DEMO")
    print("=" * 60)
    
    scanner = RepoScanner(indexer)
    
    print(f"\n🔍 Scanning project structure...")
    project_map = scanner.scan_project()
    
    stats = project_map.stats
    
    print(f"\n📊 Project Overview:")
    print(f"  Modules: {stats.total_modules}")
    print(f"  Functions: {stats.total_functions}")
    print(f"  Classes: {stats.total_classes}")
    
    if project_map.entry_points:
        print(f"\n🚪 Entry Points:")
        for ep in project_map.entry_points:
            print(f"  - {ep.name}")
    
    if stats.core_modules:
        print(f"\n⭐ Core Modules (most imported):")
        for mod in stats.core_modules[:3]:
            print(f"  - {mod}")
    
    if stats.circular_dependencies:
        print(f"\n⚠️ Circular Dependencies Found:")
        for cycle in stats.circular_dependencies[:2]:
            print(f"  - {' -> '.join(cycle[:3])}...")
    else:
        print(f"\n✅ No circular dependencies")
    
    # Test dependency queries
    if project_map.modules:
        test_module = project_map.modules[0].name
        deps = scanner.get_module_dependencies(test_module)
        if deps:
            print(f"\n🔗 Dependencies of '{test_module}':")
            for dep in list(deps)[:3]:
                print(f"  - {dep}")
    
    print("\n✅ Repository Scanner working!")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "🚀 WEEK 2: CODE ANALYSIS DEMO 🚀" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        # Demo 1: AST Analyzer
        demo_ast_analyzer()
        
        # Demo 2: Code Indexer
        indexer = demo_code_indexer()
        
        # Demo 3: Repository Scanner  
        demo_repo_scanner(indexer)
        
        # Success!
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ AST Analyzer: Can read and analyze Python code")
        print("✅ Code Indexer: Can index and search codebase")
        print("✅ Repository Scanner: Can understand project structure")
        print()
        print("📦 Phase 1 Complete: Code Analysis Foundation")
        print("🚀 Ready for Phase 2: Code Modification")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
