"""
Git Manager - Safe git operations for self-modification

This module provides git operations specifically designed for self-modification:
- Automatic backup branches
- Commits with [SELF-MODIFY] prefix
- Rollback capability
- Safety checks
"""

import git
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a commit"""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    

class GitManager:
    """
    Manages git operations for self-modification.
    
    Features:
    - Create backup branches before modifications
    - Commit with descriptive messages
    - Rollback to previous states
    - List self-modification history
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize git manager.
        
        Args:
            repo_path: Path to git repository (auto-detects if None)
        """
        if repo_path is None:
            # Auto-detect: find .git directory walking up
            repo_path = self._find_git_root()
        
        try:
            self.repo = git.Repo(repo_path)
            self.repo_path = Path(self.repo.working_dir)
            logger.info(f"GitManager initialized for {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logger.error(f"No git repository found at {repo_path}")
            raise
    
    def _find_git_root(self) -> Path:
        """Find git repository root by walking up directories"""
        current = Path.cwd()
        
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        
        raise git.InvalidGitRepositoryError("No git repository found")
    
    def create_backup_branch(self, name: Optional[str] = None) -> str:
        """
        Create a backup branch before making modifications.
        
        Args:
            name: Optional branch name (auto-generates if None)
            
        Returns:
            Name of created branch
        """
        if name is None:
            # Auto-generate name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"self-modify/backup-{timestamp}"
        
        try:
            # Create branch from current HEAD
            branch = self.repo.create_head(name)
            logger.info(f"Created backup branch: {name}")
            return name
        except Exception as e:
            logger.error(f"Failed to create backup branch: {e}")
            raise
    
    def commit_change(
        self,
        files: List[Path],
        message: str,
        tag_as_self_modify: bool = True
    ) -> str:
        """
        Commit changes to repository.
        
        Args:
            files: List of files to commit
            message: Commit message
            tag_as_self_modify: Whether to prefix with [SELF-MODIFY]
            
        Returns:
            SHA of created commit
        """
        try:
            # Add files to staging
            for filepath in files:
                # Convert to relative path from repo root
                rel_path = filepath.relative_to(self.repo_path)
                self.repo.index.add([str(rel_path)])
            
            # Prefix message if self-modify
            if tag_as_self_modify and not message.startswith("[SELF-MODIFY]"):
                message = f"[SELF-MODIFY] {message}"
            
            # Commit
            commit = self.repo.index.commit(message)
            
            logger.info(f"Committed changes: {commit.hexsha[:8]} - {message}")
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            raise
    
    def rollback_to_commit(self, sha: str, hard: bool = False) -> bool:
        """
        Rollback to a specific commit.
        
        Args:
            sha: Commit SHA to rollback to
            hard: If True, does hard reset (loses uncommitted changes)
            
        Returns:
            True if successful
        """
        try:
            if hard:
                # Hard reset - DANGEROUS!
                self.repo.head.reset(sha, index=True, working_tree=True)
                logger.warning(f"Hard reset to {sha}")
            else:
                # Soft reset - keeps changes
                self.repo.head.reset(sha, index=False, working_tree=False)
                logger.info(f"Soft reset to {sha}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return False
    
    def rollback_to_branch(self, branch_name: str) -> bool:
        """
        Rollback to a backup branch.
        
        Args:
            branch_name: Name of branch to rollback to
            
        Returns:
            True if successful
        """
        try:
            # Checkout branch
            self.repo.heads[branch_name].checkout()
            logger.info(f"Checked out branch: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to checkout branch: {e}")
            return False
    
    def create_experiment_branch(self, name: str) -> str:
        """
        Create a branch for experimenting with changes.
        
        Args:
            name: Name for experiment (will be prefixed)
            
        Returns:
            Full branch name
        """
        full_name = f"self-modify/experiment-{name}"
        
        try:
            branch = self.repo.create_head(full_name)
            branch.checkout()
            logger.info(f"Created and checked out experiment branch: {full_name}")
            return full_name
            
        except Exception as e:
            logger.error(f"Failed to create experiment branch: {e}")
            raise
    
    def get_diff(
        self,
        from_commit: Optional[str] = None,
        to_commit: str = "HEAD"
    ) -> str:
        """
        Get diff between commits.
        
        Args:
            from_commit: Starting commit (None for unstaged changes)
            to_commit: Ending commit (default: HEAD)
            
        Returns:
            Diff as string
        """
        try:
            if from_commit is None:
                # Diff of unstaged changes
                diff = self.repo.git.diff()
            else:
                # Diff between commits
                diff = self.repo.git.diff(from_commit, to_commit)
            
            return diff
            
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return ""
    
    def list_self_modifications(self, limit: int = 10) -> List[CommitInfo]:
        """
        List commits made by self-modification.
        
        Args:
            limit: Maximum number of commits to return
            
        Returns:
            List of CommitInfo objects
        """
        commits = []
        
        try:
            # Iterate through commits
            for commit in self.repo.iter_commits(max_count=limit * 2):
                # Filter for self-modify commits
                if "[SELF-MODIFY]" in commit.message:
                    commits.append(CommitInfo(
                        sha=commit.hexsha,
                        message=commit.message.strip(),
                        author=str(commit.author),
                        timestamp=datetime.fromtimestamp(commit.committed_date),
                        files_changed=[item.a_path for item in commit.diff(commit.parents[0])] if commit.parents else []
                    ))
                    
                    if len(commits) >= limit:
                        break
            
            logger.info(f"Found {len(commits)} self-modification commits")
            return commits
            
        except Exception as e:
            logger.error(f"Failed to list commits: {e}")
            return []
    
    def get_current_branch(self) -> str:
        """Get name of current branch"""
        return self.repo.active_branch.name
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        return self.repo.is_dirty()
    
    def get_status(self) -> dict:
        """
        Get repository status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'current_branch': self.get_current_branch(),
            'has_uncommitted_changes': self.has_uncommitted_changes(),
            'last_commit': self.repo.head.commit.hexsha[:8],
            'last_commit_message': self.repo.head.commit.message.strip(),
            'repo_path': str(self.repo_path)
        }
    
    def stash_changes(self, message: Optional[str] = None) -> bool:
        """
        Stash current changes.
        
        Args:
            message: Optional stash message
            
        Returns:
            True if successful
        """
        try:
            if message:
                self.repo.git.stash('save', message)
            else:
                self.repo.git.stash()
            
            logger.info("Stashed changes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stash: {e}")
            return False
    
    def pop_stash(self) -> bool:
        """
        Pop most recent stash.
        
        Returns:
            True if successful
        """
        try:
            self.repo.git.stash('pop')
            logger.info("Popped stash")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pop stash: {e}")
            return False
    
    def is_safe_to_modify(self) -> tuple[bool, str]:
        """
        Check if it's safe to make modifications.
        
        Returns:
            (is_safe, reason) tuple
        """
        # Check for uncommitted changes
        if self.has_uncommitted_changes():
            return False, "Repository has uncommitted changes"
        
        # Check if on a safe branch (not main/master)
        current_branch = self.get_current_branch()
        if current_branch in ['main', 'master', 'production']:
            return False, f"Currently on protected branch: {current_branch}"
        
        return True, "Safe to modify"


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🔧 Testing Git Manager...")
        print("=" * 60)
        
        # Initialize
        git_mgr = GitManager()
        
        # Get status
        print("\n📊 Repository Status:")
        status = git_mgr.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Check if safe to modify
        print("\n🔒 Safety Check:")
        is_safe, reason = git_mgr.is_safe_to_modify()
        if is_safe:
            print(f"  ✅ {reason}")
        else:
            print(f"  ⚠️ {reason}")
        
        # List self-modifications
        print("\n📜 Recent Self-Modifications:")
        commits = git_mgr.list_self_modifications(limit=5)
        if commits:
            for commit in commits:
                timestamp = commit.timestamp.strftime("%Y-%m-%d %H:%M")
                print(f"  - [{commit.sha[:8]}] {timestamp}")
                print(f"    {commit.message}")
                if commit.files_changed:
                    print(f"    Files: {', '.join(commit.files_changed[:3])}")
        else:
            print("  No self-modification commits found")
        
        # Test backup branch creation
        print("\n💾 Testing Backup Branch:")
        backup_branch = git_mgr.create_backup_branch()
        print(f"  ✅ Created: {backup_branch}")
        
        # Clean up test branch
        git_mgr.repo.delete_head(backup_branch)
        print(f"  🗑️ Cleaned up test branch")
        
        print("\n✅ Git Manager works!")
        
    except git.InvalidGitRepositoryError:
        print("❌ No git repository found")
        print("   (This is expected if running outside a git repo)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
