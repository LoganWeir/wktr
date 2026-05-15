import re
import hashlib
from pathlib import Path

def normalize_branch_name(branch: str) -> str:
    """
    Normalize a branch name to a safe directory name.
    Replaces '/', '\', ':', '*', '?', '"', '<', '>', '|' with '-'.
    Collapses runs of '-' and strips leading/trailing '-'.
    """
    # Replace unsafe chars with '-'
    safe = re.sub(r'[\\/:*?"<>|]', '-', branch)
    # Collapse runs of '-'
    safe = re.sub(r'-+', '-', safe)
    # Strip leading/trailing '-'
    return safe.strip('-')

def branch_to_dirname(branch: str, worktrees_root: Path, existing_branches: dict[str, str] = None) -> str:
    """
    Convert a branch name to a directory name.
    If the target path exists for a different branch, append a short SHA1 of the branch name.
    existing_branches is a mapping of dirname -> branch_name for existing worktrees.
    """
    base_name = normalize_branch_name(branch)
    if not base_name:
        base_name = "worktree"
        
    target_dir = worktrees_root / base_name
    
    # If the directory exists, check if it belongs to the same branch
    if target_dir.exists():
        if existing_branches and existing_branches.get(base_name) == branch:
            return base_name
        # Collision: append short sha1
        sha = hashlib.sha1(branch.encode('utf-8')).hexdigest()[:7]
        return f"{base_name}--{sha}"
        
    return base_name
