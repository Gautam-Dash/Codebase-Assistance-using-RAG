"""Commit-aware context module for git-based code understanding."""
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    import git
    from git.objects.commit import Commit as GitCommit
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    GitCommit = None

from src.utils.models import CodeChunk, CommitContext, ContextualResult, RankedResult
from src.utils.logger import logger


class GitContextManager:
    """Manages git repository context for code chunks."""

    def __init__(self, repo_path: Path):
        """
        Initialize git context manager.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = repo_path
        self.repo = None
        
        if not GIT_AVAILABLE:
            logger.warning("GitPython not available. Git context features will be disabled.")
            return
        
        try:
            self.repo = git.Repo(repo_path)
            logger.info(f"Loaded git repository from {repo_path}")
        except Exception as e:
            logger.warning(f"Could not initialize git repository: {e}")
            self.repo = None

    def get_file_commits(
        self,
        file_path: str,
        limit: int = 10
    ) -> List[CommitContext]:
        """
        Get commits for a specific file.

        Args:
            file_path: Relative path to file
            limit: Maximum number of commits to return

        Returns:
            List of commit contexts
        """
        if not self.repo:
            return []

        commits = []
        try:
            # Get commits for this file
            git_commits = list(self.repo.iter_commits(paths=file_path, max_count=limit))

            for commit in git_commits:
                context = self._extract_commit_context(commit, file_path)
                commits.append(context)

        except Exception as e:
            logger.warning(f"Failed to get commits for {file_path}: {e}")

        return commits

    def get_chunk_commits(
        self,
        chunk: CodeChunk,
        limit: int = 5
    ) -> List[CommitContext]:
        """
        Get relevant commits for a code chunk.

        Args:
            chunk: Code chunk
            limit: Maximum commits to return

        Returns:
            List of relevant commit contexts
        """
        if not self.repo:
            return []

        try:
            # Get blame information for the chunk
            file_path = Path(chunk.file_path).relative_to(self.repo_path)
            commits = self.repo.blame("HEAD", str(file_path))

            chunk_commits = {}
            for commit, lines in commits:
                # Check if any blamed lines fall within chunk range
                if self._overlaps_chunk(lines, chunk.start_line, chunk.end_line):
                    chunk_commits[commit.hexsha] = commit

            # Convert to contexts and limit
            contexts = [
                self._extract_commit_context(commit, str(file_path))
                for commit in list(chunk_commits.values())[:limit]
            ]

            return contexts

        except Exception as e:
            logger.warning(f"Failed to get blame info for {chunk.file_path}: {e}")
            return []

    def get_related_changes(
        self,
        chunk: CodeChunk,
        lookback_commits: int = 20
    ) -> List[str]:
        """
        Find other files changed together with this chunk.

        Args:
            chunk: Code chunk
            lookback_commits: Number of commits to look back

        Returns:
            List of related file paths
        """
        if not self.repo:
            return []

        try:
            file_path = Path(chunk.file_path).relative_to(self.repo_path)
            git_commits = list(self.repo.iter_commits(paths=str(file_path), max_count=lookback_commits))

            related_files = set()
            for commit in git_commits:
                for item in commit.tree.traverse():
                    if item.type == "blob":
                        related_files.add(item.path)

            # Remove the chunk's own file
            related_files.discard(str(file_path))

            return list(related_files)

        except Exception as e:
            logger.warning(f"Failed to get related changes for {chunk.file_path}: {e}")
            return []

    def get_commit_history(
        self,
        file_path: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get commit history for a file.

        Args:
            file_path: Relative path to file
            limit: Maximum commits to return

        Returns:
            List of commit information dictionaries
        """
        if not self.repo:
            return []

        history = []
        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=limit))

            for commit in commits:
                history.append({
                    "hash": commit.hexsha[:7],
                    "author": commit.author.name,
                    "date": datetime.fromtimestamp(commit.committed_date),
                    "message": commit.message.strip(),
                    "insertions": 0,  # Would need to calculate from stats
                    "deletions": 0
                })

        except Exception as e:
            logger.warning(f"Failed to get commit history for {file_path}: {e}")

        return history

    def _extract_commit_context(
        self,
        commit: GitCommit,
        file_path: str
    ) -> CommitContext:
        """Extract context information from a git commit."""
        return CommitContext(
            commit_hash=commit.hexsha[:7],
            author=commit.author.name,
            date=datetime.fromtimestamp(commit.committed_date),
            message=commit.message.strip(),
            changed_files=self._get_changed_files(commit),
            insertions=self._get_insertions(commit),
            deletions=self._get_deletions(commit)
        )

    def _overlaps_chunk(self, lines: List, start: int, end: int) -> bool:
        """Check if blamed lines overlap with chunk range."""
        for line in lines:
            if start <= line <= end:
                return True
        return False

    @staticmethod
    def _get_changed_files(commit: GitCommit) -> List[str]:
        """Get list of files changed in commit."""
        try:
            if commit.parents:
                changed = commit.parents[0].tree.diff_to_tree(commit.tree)
                return [item.path for item in changed]
        except Exception:
            pass
        return []

    @staticmethod
    def _get_insertions(commit: GitCommit) -> int:
        """Get number of insertions in commit."""
        try:
            stats = commit.stats.total
            return stats.get("insertions", 0)
        except Exception:
            return 0

    @staticmethod
    def _get_deletions(commit: GitCommit) -> int:
        """Get number of deletions in commit."""
        try:
            stats = commit.stats.total
            return stats.get("deletions", 0)
        except Exception:
            return 0


class ContextualRetriever:
    """Adds contextual information to retrieved results."""

    def __init__(self, git_context: GitContextManager):
        """
        Initialize contextual retriever.

        Args:
            git_context: GitContextManager instance
        """
        self.git_context = git_context

    def enrich_results(
        self,
        ranked_results: List[RankedResult],
        include_history: bool = True,
        include_related: bool = True
    ) -> List[ContextualResult]:
        """
        Enrich ranked results with contextual information.

        Args:
            ranked_results: Re-ranked retrieval results
            include_history: Include commit history
            include_related: Include related changes

        Returns:
            Contextual results with additional metadata
        """
        contextual_results = []

        for ranked_result in ranked_results:
            chunk = ranked_result.result.chunk

            # Get commit context
            commit_context = None
            commits = self.git_context.get_chunk_commits(chunk, limit=1)
            if commits:
                commit_context = commits[0]

            # Get related chunks
            related_chunks = []
            if include_related:
                related_files = self.git_context.get_related_changes(chunk)
                # In a full implementation, would retrieve chunks from these files
                # For now, just store the file paths

            contextual_result = ContextualResult(
                ranked_result=ranked_result,
                commit_context=commit_context,
                related_chunks=related_chunks
            )

            contextual_results.append(contextual_result)

        return contextual_results

    def get_impact_analysis(self, chunk: CodeChunk) -> Dict[str, Any]:
        """
        Analyze the impact and context of a code chunk.

        Args:
            chunk: Code chunk to analyze

        Returns:
            Dictionary with impact analysis information
        """
        commits = self.git_context.get_file_commits(chunk.file_path, limit=10)
        related_files = self.git_context.get_related_changes(chunk)

        recent_change = commits[0] if commits else None
        recent_author = recent_change.author if recent_change else "Unknown"

        return {
            "chunk_id": chunk.chunk_id,
            "file_path": chunk.file_path,
            "last_modified_by": recent_author,
            "last_modified_date": recent_change.date if recent_change else None,
            "commit_count": len(commits),
            "related_files_count": len(related_files),
            "recent_commits": [
                {
                    "hash": c.commit_hash,
                    "message": c.message,
                    "date": c.date.isoformat()
                }
                for c in commits[:3]
            ]
        }
