# Week 2: Self-Modification Engine - Architectuur

**Doel:** Omni kan zichzelf analyseren, verbeteren en hot-reloaden zonder restart.

---

## 🏗️ High-Level Architectuur

```
┌────────────────────────────────────────────────────────────────┐
│                        META AGENT                              │
│                  (Orchestrates self-improvement)               │
└────┬───────────────────────────────────────────────────────┬───┘
     │                                                       │
     │  ┌────────────────────────────────────────────────┐  │
     └──┤        SELF-IMPROVEMENT PIPELINE               │◄─┘
        │                                                │
        │  1. OBSERVE   → Detect issues/bottlenecks     │
        │  2. ANALYZE   → Identify root cause           │
        │  3. DESIGN    → Plan solution                 │
        │  4. IMPLEMENT → Generate code                 │
        │  5. TEST      → Validate changes              │
        │  6. DEPLOY    → Apply + hot-reload            │
        │  7. ROLLBACK  → Revert if failed              │
        └────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  CODE ANALYSIS   │  │  CODE MODIFICATION│  │  MULTI-AGENTS    │
│                  │  │                   │  │                  │
│ • AST Analyzer   │  │ • Code Rewriter   │  │ • Observer       │
│ • Code Indexer   │  │ • Git Manager     │  │ • Analyzer       │
│ • Repo Scanner   │  │ • Hot Reloader    │  │ • Coder          │
│                  │  │                   │  │ • Tester         │
│                  │  │                   │  │ • Deployer       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 📦 Component Overview

### Phase 1: Code Analysis Foundation (Dag 1-2)

#### 1.1 AST Analyzer (`backend/self_modify/ast_analyzer.py`)

**Purpose:** Parse en analyseer Python code veilig

```python
class ASTAnalyzer:
    """Analyzes Python code using Abstract Syntax Trees"""
    
    def parse_file(self, filepath: Path) -> ast.Module:
        """Parse Python file to AST"""
        
    def find_functions(self, module: ast.Module) -> List[ast.FunctionDef]:
        """Extract all function definitions"""
        
    def find_classes(self, module: ast.Module) -> List[ast.ClassDef]:
        """Extract all class definitions"""
        
    def extract_imports(self, module: ast.Module) -> List[ImportInfo]:
        """Extract import statements with line numbers"""
        
    def analyze_function_signature(self, func: ast.FunctionDef) -> FunctionSignature:
        """Analyze parameters, return types, decorators"""
        
    def find_function_calls(self, node: ast.AST, target: str) -> List[CallSite]:
        """Find all calls to a specific function"""
        
    def build_dependency_graph(self) -> nx.DiGraph:
        """Build graph of function/class dependencies"""
```

**Key Features:**
- Safe parsing (catches SyntaxError)
- Line number tracking voor alle nodes
- Type hint extraction
- Decorator analysis
- Docstring extraction

#### 1.2 Code Indexer (`backend/self_modify/code_index.py`)

**Purpose:** Index hele codebase + incremental updates

```python
class CodeIndexer:
    """Maintains searchable index of codebase"""
    
    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.index = {}  # filepath -> FileIndex
        self.watcher = None  # watchdog.Observer
        
    def index_codebase(self) -> Dict[Path, FileIndex]:
        """Initial full scan of all Python files"""
        
    def on_file_changed(self, event: FileSystemEvent):
        """Handle file change from watchdog"""
        
    def search_pattern(self, pattern: str, use_regex: bool = False) -> List[Match]:
        """Search for pattern in indexed code"""
        
    def find_definition(self, symbol: str) -> Optional[Location]:
        """Find where symbol is defined"""
        
    def find_references(self, symbol: str) -> List[Location]:
        """Find all references to symbol"""
        
    def get_file_stats(self, filepath: Path) -> FileStats:
        """Get LOC, complexity, etc."""
```

**Data Structures:**
```python
@dataclass
class FileIndex:
    filepath: Path
    ast_module: ast.Module
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    last_modified: float
    hash: str  # For change detection

@dataclass
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    signature: FunctionSignature
    docstring: Optional[str]
    complexity: int  # Cyclomatic complexity
    calls: List[str]  # Functions this calls
```

#### 1.3 Repository Scanner (`backend/self_modify/repo_scanner.py`)

**Purpose:** High-level project structure understanding

```python
class RepoScanner:
    """Scans and understands project structure"""
    
    def scan_project(self, root: Path) -> ProjectMap:
        """Build map of entire project"""
        
    def identify_core_modules(self) -> List[ModuleInfo]:
        """Find core modules (most imported)"""
        
    def find_entry_points(self) -> List[Path]:
        """Find main.py, __main__.py, etc."""
        
    def detect_test_files(self) -> List[Path]:
        """Find test files"""
        
    def build_module_graph(self) -> nx.DiGraph:
        """Graph of module dependencies"""
        
    def find_circular_dependencies(self) -> List[Cycle]:
        """Detect import cycles"""
```

**Output:**
```python
@dataclass
class ProjectMap:
    root: Path
    modules: List[ModuleInfo]
    entry_points: List[Path]
    test_files: List[Path]
    dependency_graph: nx.DiGraph
    stats: ProjectStats
    
@dataclass
class ModuleInfo:
    path: Path
    name: str
    imports: List[str]
    exported_symbols: List[str]
    is_core: bool  # Frequently imported
    import_count: int  # How many files import this
```

---

### Phase 2: Code Modification (Dag 3-4)

#### 2.1 Safe Code Rewriter (`backend/self_modify/code_rewriter.py`)

**Purpose:** Modify Python code veilig met formatting preserved

```python
class SafeCodeRewriter:
    """Safely modifies Python code using libcst"""
    
    def __init__(self):
        self.git_manager = GitManager()
        
    def modify_function(
        self,
        filepath: Path,
        func_name: str,
        new_body: str
    ) -> ChangeResult:
        """Replace function body"""
        # 1. Parse with libcst (preserves whitespace/comments)
        # 2. Find function node
        # 3. Replace body
        # 4. Validate syntax
        # 5. Create git backup
        # 6. Write file
        
    def add_import(self, filepath: Path, import_stmt: str) -> ChangeResult:
        """Add import at top of file"""
        
    def add_decorator(self, filepath: Path, func_name: str, decorator: str):
        """Add decorator to function"""
        
    def refactor_to_async(self, filepath: Path, func_name: str):
        """Convert sync function to async"""
        
    def add_function(self, filepath: Path, func_code: str, after: Optional[str] = None):
        """Insert new function"""
        
    def remove_function(self, filepath: Path, func_name: str):
        """Remove function (with backup)"""
```

**Key Features:**
- **libcst** voor formatting preservation
- Syntax validation voor/na changes
- Automatic git backup
- Rollback capability
- Change preview (diff)

#### 2.2 Git Manager (`backend/self_modify/git_manager.py`)

**Purpose:** Version control voor self-modifications

```python
class GitManager:
    """Manages git operations for self-modification"""
    
    def __init__(self, repo_path: Path):
        self.repo = git.Repo(repo_path)
        
    def create_backup_branch(self, name: str = None) -> str:
        """Create branch before modification"""
        # Format: self-modify/backup-{timestamp}
        
    def commit_change(self, files: List[Path], message: str):
        """Commit self-modification"""
        
    def rollback_to_commit(self, sha: str):
        """Rollback to specific commit"""
        
    def create_experiment_branch(self, name: str) -> str:
        """Create branch for testing changes"""
        # Format: self-modify/experiment-{name}
        
    def get_diff(self, from_sha: str, to_sha: str = "HEAD") -> str:
        """Get diff between commits"""
        
    def list_self_modifications(self) -> List[Commit]:
        """List commits made by self-modification"""
        # Filter by commit message prefix: "[SELF-MODIFY]"
```

**Workflow:**
```python
# Before modification:
backup_branch = git.create_backup_branch()

# Make changes...
rewriter.modify_function(...)

# Test changes...
if tests_pass:
    git.commit_change(files, "[SELF-MODIFY] Optimized chat() with caching")
else:
    git.rollback_to_commit(backup_branch)
```

#### 2.3 Hot Reloader (`backend/self_modify/hot_reload.py`)

**Purpose:** Reload Python modules zonder Electron restart

```python
class HotReloader:
    """Reloads Python modules at runtime"""
    
    def __init__(self):
        self.watched_modules = {}  # module_name -> module_obj
        self.file_watcher = Observer()  # watchdog
        
    def watch_directory(self, path: Path):
        """Start watching directory for changes"""
        
    def reload_module(self, module_name: str) -> ReloadResult:
        """Reload single module"""
        # 1. importlib.reload(module)
        # 2. Update global references
        # 3. Re-initialize if needed
        # 4. Notify Electron main process
        
    def reload_all_changed(self) -> List[ReloadResult]:
        """Reload all modules that changed"""
        
    def on_file_modified(self, event: FileModifiedEvent):
        """Callback from watchdog"""
        # Debounce rapid changes
        # Identify affected modules
        # Reload in dependency order
        
    def register_hot_reloadable(self, module_name: str, reinit_func: Callable):
        """Register module with custom reinit logic"""
```

**Challenges:**
- Module references in other modules
- Singleton pattern handling
- Event handler re-registration
- State preservation

**Solution:**
```python
# In backend/main.py
class OmniBackend:
    def __init__(self):
        self.llm = None
        self.memory = None
        self.hot_reloader = HotReloader()
        self.hot_reloader.register_hot_reloadable(
            "core.llm_client",
            self._reinit_llm
        )
        
    def _reinit_llm(self):
        """Reinitialize LLM after hot-reload"""
        self.llm = LLMClient(...)
```

---

### Phase 3: Multi-Agent System (Dag 5-8)

#### 3.1 Base Agent (`backend/agents/base_agent.py`)

```python
class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, llm_client: LLMClient, name: str):
        self.llm = llm_client
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        
    @abstractmethod
    async def process(self, input_data: Any) -> AgentResult:
        """Process input and return result"""
        pass
        
    def log_action(self, action: str, details: dict):
        """Log agent action for audit trail"""
        
    async def think(self, prompt: str) -> str:
        """Use LLM to reason about task"""
        # Structured prompt with role/context
        return await self.llm.generate(prompt)
```

#### 3.2 Observer Agent (`backend/agents/observer.py`)

**Purpose:** Monitor performance & detect issues

```python
class ObserverAgent(BaseAgent):
    """Monitors system performance and code quality"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(llm, "Observer")
        self.metrics = {}
        self.performance_log = []
        
    async def monitor_function_performance(
        self,
        func_name: str,
        execution_time: float
    ):
        """Track function performance"""
        if func_name not in self.metrics:
            self.metrics[func_name] = []
        self.metrics[func_name].append(execution_time)
        
    async def detect_bottlenecks(self) -> List[Bottleneck]:
        """Find slow functions"""
        bottlenecks = []
        for func, times in self.metrics.items():
            avg_time = statistics.mean(times)
            if avg_time > 1.0:  # Threshold
                bottlenecks.append(Bottleneck(
                    function=func,
                    avg_time=avg_time,
                    call_count=len(times),
                    severity="high" if avg_time > 2.0 else "medium"
                ))
        return bottlenecks
        
    async def analyze_error_patterns(self) -> List[ErrorPattern]:
        """Detect recurring errors"""
        # Parse logs, find patterns
        
    async def suggest_improvements(self) -> List[Suggestion]:
        """Use LLM to suggest improvements"""
        prompt = f"""
        Performance metrics:
        {json.dumps(self.metrics, indent=2)}
        
        Analyze and suggest 3 concrete improvements.
        Focus on: caching, async/await, algorithms.
        """
        response = await self.think(prompt)
        return self._parse_suggestions(response)
```

**Output:**
```python
@dataclass
class Bottleneck:
    function: str
    avg_time: float
    call_count: int
    severity: str  # "low", "medium", "high"
    stack_trace: Optional[str]
    
@dataclass
class Suggestion:
    title: str
    description: str
    target_function: str
    expected_improvement: str  # "2x faster", "50% less memory"
    difficulty: str  # "easy", "medium", "hard"
```

#### 3.3 Analyzer Agent (`backend/agents/analyzer.py`)

**Purpose:** Analyze code voor optimization opportunities

```python
class AnalyzerAgent(BaseAgent):
    """Analyzes code patterns and quality"""
    
    def __init__(self, llm: LLMClient, ast_analyzer: ASTAnalyzer):
        super().__init__(llm, "Analyzer")
        self.ast = ast_analyzer
        
    async def analyze_bottleneck(self, bottleneck: Bottleneck) -> Analysis:
        """Deep dive into bottleneck cause"""
        # 1. Get function source
        func_node = self.ast.find_function(bottleneck.function)
        source = ast.unparse(func_node)
        
        # 2. LLM analysis
        prompt = f"""
        This function is slow ({bottleneck.avg_time:.2f}s average):
        
        ```python
        {source}
        ```
        
        Identify the root cause. Consider:
        - Unnecessary computations
        - Missing caching
        - Blocking I/O
        - Inefficient algorithms
        - Database queries in loops
        
        Respond in JSON:
        {{
            "root_cause": "...",
            "explanation": "...",
            "recommendation": "..."
        }}
        """
        response = await self.think(prompt)
        return Analysis.from_json(response)
        
    async def find_code_smells(self, filepath: Path) -> List[CodeSmell]:
        """Detect anti-patterns"""
        # God classes, long functions, deep nesting
        
    async def find_optimization_opportunities(self) -> List[Opportunity]:
        """Find potential optimizations"""
        # Cacheable functions, parallelizable loops
```

#### 3.4 Coder Agent (`backend/agents/coder.py`)

**Purpose:** Generate code improvements

```python
class CoderAgent(BaseAgent):
    """Generates code solutions"""
    
    def __init__(self, llm: LLMClient, rewriter: SafeCodeRewriter):
        super().__init__(llm, "Coder")
        self.rewriter = rewriter
        
    async def implement_fix(
        self,
        analysis: Analysis,
        target_function: str
    ) -> CodeChange:
        """Generate code to fix issue"""
        
        # Get current function
        func_source = self._get_function_source(target_function)
        
        # LLM code generation
        prompt = f"""
        Improve this function based on analysis:
        
        **Current code:**
        ```python
        {func_source}
        ```
        
        **Issue:** {analysis.root_cause}
        **Recommendation:** {analysis.recommendation}
        
        Generate improved version. Requirements:
        - Preserve function signature
        - Add type hints
        - Add docstring explaining change
        - Include necessary imports
        - Follow PEP 8
        
        Respond with ONLY the new function code.
        """
        
        new_code = await self.think(prompt)
        
        # Validate syntax
        try:
            ast.parse(new_code)
        except SyntaxError as e:
            self.logger.error(f"Generated code has syntax error: {e}")
            return None
            
        return CodeChange(
            target=target_function,
            old_code=func_source,
            new_code=new_code,
            analysis=analysis
        )
        
    async def generate_test(self, function: str) -> str:
        """Generate pytest test for function"""
```

#### 3.5 Tester Agent (`backend/agents/tester.py`)

**Purpose:** Validate changes

```python
class TesterAgent(BaseAgent):
    """Tests and validates changes"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(llm, "Tester")
        
    async def validate_change(self, change: CodeChange) -> TestResult:
        """Run tests on code change"""
        
        # 1. Apply change temporarily
        with TemporaryChange(change) as temp:
            # 2. Run pytest
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True
            )
            
            # 3. Run benchmarks
            old_time = self._benchmark_function(change.target, change.old_code)
            new_time = self._benchmark_function(change.target, change.new_code)
            
            return TestResult(
                passed=result.returncode == 0,
                test_output=result.stdout,
                old_performance=old_time,
                new_performance=new_time,
                improvement=old_time / new_time if new_time > 0 else 0
            )
            
    async def run_safety_checks(self, change: CodeChange) -> SafetyReport:
        """Check for security issues"""
        # Use bandit for security scanning
```

#### 3.6 Deployer Agent (`backend/agents/deployer.py`)

**Purpose:** Apply changes safely

```python
class DeployerAgent(BaseAgent):
    """Deploys validated changes"""
    
    def __init__(
        self,
        llm: LLMClient,
        git: GitManager,
        hot_reloader: HotReloader
    ):
        super().__init__(llm, "Deployer")
        self.git = git
        self.hot_reloader = hot_reloader
        
    async def deploy_change(
        self,
        change: CodeChange,
        test_result: TestResult
    ) -> DeployResult:
        """Apply change to codebase"""
        
        # 1. Create backup
        backup_branch = self.git.create_backup_branch()
        
        try:
            # 2. Apply change
            self.rewriter.modify_function(
                change.filepath,
                change.target,
                change.new_code
            )
            
            # 3. Git commit
            self.git.commit_change(
                [change.filepath],
                f"[SELF-MODIFY] {change.analysis.title}\n\n"
                f"Improvement: {test_result.improvement:.1f}x faster"
            )
            
            # 4. Hot-reload
            reload_result = self.hot_reloader.reload_module(
                change.module_name
            )
            
            # 5. Verify still works
            if not await self._verify_system_health():
                raise DeploymentError("System health check failed")
                
            return DeployResult(
                success=True,
                backup_branch=backup_branch,
                commit_sha=self.git.repo.head.commit.hexsha
            )
            
        except Exception as e:
            # Rollback on failure
            self.git.rollback_to_commit(backup_branch)
            self.hot_reloader.reload_all_changed()
            return DeployResult(success=False, error=str(e))
```

#### 3.7 Meta Agent (`backend/agents/meta_agent.py`)

**Purpose:** Orchestrates entire self-improvement pipeline

```python
class MetaAgent:
    """Orchestrates self-improvement workflow"""
    
    def __init__(
        self,
        llm: LLMClient,
        observer: ObserverAgent,
        analyzer: AnalyzerAgent,
        coder: CoderAgent,
        tester: TesterAgent,
        deployer: DeployerAgent
    ):
        self.llm = llm
        self.observer = observer
        self.analyzer = analyzer
        self.coder = coder
        self.tester = tester
        self.deployer = deployer
        self.improvement_log = []
        
    async def run_improvement_cycle(self) -> ImprovementResult:
        """Complete self-improvement cycle"""
        
        self.logger.info("🚀 Starting self-improvement cycle")
        
        # 1. OBSERVE - Find issues
        self.logger.info("👁️ Observer: Detecting bottlenecks...")
        bottlenecks = await self.observer.detect_bottlenecks()
        
        if not bottlenecks:
            self.logger.info("✅ No bottlenecks found")
            return ImprovementResult(status="no_action_needed")
            
        # Pick worst bottleneck
        target = max(bottlenecks, key=lambda b: b.avg_time)
        self.logger.info(f"🎯 Target: {target.function} ({target.avg_time:.2f}s)")
        
        # 2. ANALYZE - Root cause
        self.logger.info("🔍 Analyzer: Analyzing root cause...")
        analysis = await self.analyzer.analyze_bottleneck(target)
        self.logger.info(f"💡 Root cause: {analysis.root_cause}")
        
        # 3. IMPLEMENT - Generate fix
        self.logger.info("👨‍💻 Coder: Generating fix...")
        change = await self.coder.implement_fix(analysis, target.function)
        
        if not change:
            return ImprovementResult(status="failed", reason="Code generation failed")
            
        # 4. TEST - Validate
        self.logger.info("🧪 Tester: Validating change...")
        test_result = await self.tester.validate_change(change)
        
        if not test_result.passed:
            self.logger.warning("❌ Tests failed, aborting")
            return ImprovementResult(
                status="failed",
                reason="Tests failed",
                test_output=test_result.test_output
            )
            
        self.logger.info(f"✅ Tests passed! Improvement: {test_result.improvement:.1f}x")
        
        # 5. DEPLOY - Apply change
        self.logger.info("🚀 Deployer: Applying change...")
        deploy_result = await self.deployer.deploy_change(change, test_result)
        
        if not deploy_result.success:
            self.logger.error(f"❌ Deployment failed: {deploy_result.error}")
            return ImprovementResult(status="failed", reason=deploy_result.error)
            
        # 6. SUCCESS!
        self.logger.info(f"🎉 Self-improvement successful!")
        
        result = ImprovementResult(
            status="success",
            target_function=target.function,
            improvement=test_result.improvement,
            commit_sha=deploy_result.commit_sha,
            backup_branch=deploy_result.backup_branch
        )
        
        self.improvement_log.append(result)
        
        # 7. Notify user
        await self._notify_user(result)
        
        return result
        
    async def _notify_user(self, result: ImprovementResult):
        """Send notification to Electron UI"""
        # Via JSON-RPC notification
        notification = {
            "type": "self_improvement",
            "title": "✨ Self-Improvement Complete!",
            "message": (
                f"Optimized {result.target_function}\n"
                f"Performance: {result.improvement:.1f}x faster"
            ),
            "action": "view_diff",
            "commit": result.commit_sha
        }
        # Send to Electron main process
```

---

## 🔄 Complete Self-Improvement Flow

```
┌─────────────────────────────────────────────────────────┐
│                     USER USES OMNI                      │
│                  (Chat, Memory, etc.)                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  OBSERVER MONITORS   │
              │  • Function calls    │
              │  • Execution times   │
              │  • Error rates       │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  DETECT BOTTLENECK   │
              │  chat() = 2.5s avg   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  ANALYZER EXAMINES   │
              │  Root cause:         │
              │  • No caching        │
              │  • Recomputes embed  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  CODER GENERATES     │
              │  Fix: Add @lru_cache │
              │  to embedding func   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  TESTER VALIDATES    │
              │  • Tests pass ✅     │
              │  • 4x faster ✅      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  DEPLOYER APPLIES    │
              │  • Git commit        │
              │  • Hot-reload        │
              │  • Verify works      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  NOTIFY USER         │
              │  "✨ Improved 4x!"   │
              └──────────────────────┘
```

---

## 📊 Data Flow

### Performance Monitoring

```python
# Decorator tracks all function calls
@track_performance
async def chat(message: str) -> str:
    # ... actual chat logic
    pass

# Observer records
observer.monitor_function_performance("chat", execution_time=2.5)
```

### Agent Communication

```python
@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str
    message_type: str  # "task", "result", "question"
    payload: dict
    timestamp: float
    
# Example:
observer -> analyzer: {
    "type": "bottleneck_detected",
    "function": "chat",
    "metrics": {...}
}

analyzer -> coder: {
    "type": "fix_request",
    "analysis": {...},
    "target": "chat"
}
```

---

## 🔐 Safety Mechanisms

### 1. Git Backup
```python
# Before every change
backup = git.create_backup_branch()
# Try change...
if failed:
    git.rollback_to_commit(backup)
```

### 2. Test Validation
```python
# No deploy without passing tests
if not test_result.passed:
    return abort()
```

### 3. Health Checks
```python
async def _verify_system_health():
    # Check critical functions still work
    try:
        await test_chat()
        await test_memory()
        await test_embeddings()
        return True
    except:
        return False
```

### 4. Rate Limiting
```python
# Max 1 self-modification per 5 minutes
@rate_limit(max_per_hour=12)
async def run_improvement_cycle():
    ...
```

### 5. User Approval (Optional)
```python
# For high-risk changes
if change.risk_level == "high":
    approval = await request_user_approval(change)
    if not approval:
        return abort()
```

---

## 📈 Success Metrics

**Week 2 Goals:**
- ✅ Kan eigen code lezen (AST)
- ✅ Kan code wijzigen (libcst)
- ✅ Kan hot-reloaden
- ✅ Multi-agent system werkt
- ✅ **1 succesvolle autonomous improvement**

**Metingen:**
- Improvement count
- Success rate
- Performance gain (avg speedup)
- Rollback rate
- Time to improvement

---

## 🚀 Implementation Plan

### Dag 1-2: Code Analysis
- [x] Setup `backend/self_modify/` structure
- [ ] Implement `ast_analyzer.py`
- [ ] Implement `code_indexer.py`
- [ ] Implement `repo_scanner.py`
- [ ] Test: Can Omni read its own code?

### Dag 3-4: Code Modification
- [ ] Implement `code_rewriter.py` (libcst)
- [ ] Implement `git_manager.py`
- [ ] Implement `hot_reload.py`
- [ ] Test: Can Omni modify itself and reload?

### Dag 5-8: Multi-Agent System
- [ ] Create `backend/agents/` structure
- [ ] Implement `base_agent.py`
- [ ] Implement `observer.py`
- [ ] Implement `analyzer.py`
- [ ] Implement `coder.py`
- [ ] Implement `tester.py`
- [ ] Implement `deployer.py`
- [ ] Implement `meta_agent.py`
- [ ] Test: Does pipeline work end-to-end?

### Dag 9: First Improvement
- [ ] Run complete improvement cycle
- [ ] Verify change applied successfully
- [ ] Measure performance gain
- [ ] Record demo video

### Dag 10: Polish & Docs
- [ ] Add UI for viewing improvements
- [ ] Write WEEK2_COMPLETE.md
- [ ] Create demo video
- [ ] Prepare for Week 3

---

## 📝 Notes

**Dependencies to install:**
```bash
pip install libcst watchdog GitPython networkx pytest bandit
```

**Challenges verwacht:**
- Hot-reloading met singleton patterns
- Rollback van complex changes
- LLM code generation quality
- Test coverage voor kritieke functies

**Mitigaties:**
- Start met simpele changes (decorators, caching)
- Extensive testing voor elk change
- User can manually review high-risk changes
- Always keep backup branches

---

**Next:** Start met `ast_analyzer.py`! 🚀
