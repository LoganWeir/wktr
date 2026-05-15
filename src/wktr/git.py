import subprocess
from pathlib import Path
from typing import Optional, List

class GitError(Exception):
    pass

def run_git(args: List[str], cwd: Optional[Path] = None, timeout: float = 5.0, check: bool = True) -> str:
    """
    Run a git command and return its stdout.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        raise GitError(f"Git command timed out after {timeout}s: {' '.join(args)}") from e
    except subprocess.CalledProcessError as e:
        if check:
            raise GitError(f"Git command failed (exit code {e.returncode}): {' '.join(args)}\n{e.stderr.strip()}") from e
        return e.stdout.strip()
    except FileNotFoundError as e:
        raise GitError("git executable not found") from e

def check_ref_format(branch: str) -> bool:
    """Check if a branch name is valid."""
    try:
        run_git(["check-ref-format", "--branch", branch])
        return True
    except GitError:
        return False

def get_head_mtime(cwd: Path) -> Optional[int]:
    """Get the commit time of HEAD."""
    try:
        out = run_git(["log", "-1", "--format=%ct", "HEAD"], cwd=cwd, timeout=2.0)
        if out:
            return int(out)
    except (GitError, ValueError):
        pass
    return None
