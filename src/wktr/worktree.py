from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import concurrent.futures
from wktr.git import run_git, GitError, get_head_mtime

@dataclass
class WorktreeStatus:
    is_clean: bool = True
    ahead: Optional[int] = None
    behind: Optional[int] = None
    is_detached: bool = False
    detached_at: Optional[str] = None
    is_locked: bool = False
    is_gone: bool = False
    is_main: bool = False

@dataclass
class Worktree:
    path: Path
    branch: str
    mtime: int
    status: WorktreeStatus

def parse_worktree_list(cwd: Path) -> List[dict]:
    """
    Run git worktree list --porcelain and parse the output.
    """
    try:
        # Auto-prune first
        run_git(["worktree", "prune"], cwd=cwd, check=False)
        
        out = run_git(["worktree", "list", "--porcelain"], cwd=cwd)
    except GitError:
        return []
        
    worktrees = []
    current_wt = {}
    
    for line in out.splitlines():
        if not line:
            if current_wt:
                worktrees.append(current_wt)
                current_wt = {}
            continue
            
        parts = line.split(" ", 1)
        key = parts[0]
        val = parts[1] if len(parts) > 1 else ""
        
        if key == "worktree":
            current_wt["path"] = Path(val)
        elif key == "branch":
            # refs/heads/branch-name
            current_wt["branch"] = val.replace("refs/heads/", "")
        elif key == "detached":
            current_wt["detached"] = True
        elif key == "locked":
            current_wt["locked"] = True
        elif key == "prunable":
            current_wt["prunable"] = True
            
    if current_wt:
        worktrees.append(current_wt)
        
    return worktrees

def enrich_worktree(wt_dict: dict, is_main: bool) -> Worktree:
    path = wt_dict["path"]
    branch = wt_dict.get("branch", "")
    is_detached = wt_dict.get("detached", False)
    is_locked = wt_dict.get("locked", False)
    is_gone = wt_dict.get("prunable", False) or not path.exists()
    
    status = WorktreeStatus(
        is_detached=is_detached,
        is_locked=is_locked,
        is_gone=is_gone,
        is_main=is_main
    )
    
    mtime = 0
    if path.exists():
        mtime = get_head_mtime(path) or int(path.stat().st_mtime)
        
        if is_detached:
            try:
                sha = run_git(["rev-parse", "--short", "HEAD"], cwd=path, timeout=2.0)
                status.detached_at = sha
            except GitError:
                status.detached_at = "unknown"
                
        if not is_gone:
            try:
                # Check if clean
                status_out = run_git(["status", "--porcelain"], cwd=path, timeout=2.0)
                status.is_clean = len(status_out) == 0
                
                # Check ahead/behind
                if branch:
                    ab_out = run_git(["rev-list", "--left-right", "--count", f"{branch}...@{'{u}'}"], cwd=path, timeout=2.0, check=False)
                    if ab_out and not ab_out.startswith("fatal"):
                        parts = ab_out.split()
                        if len(parts) == 2:
                            status.ahead = int(parts[0])
                            status.behind = int(parts[1])
            except GitError:
                pass
                
    return Worktree(
        path=path,
        branch=branch,
        mtime=mtime,
        status=status
    )

def get_worktrees(cwd: Path) -> List[Worktree]:
    wt_dicts = parse_worktree_list(cwd)
    if not wt_dicts:
        return []
        
    # First one is always main
    worktrees = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for i, wt_dict in enumerate(wt_dicts):
            futures.append(executor.submit(enrich_worktree, wt_dict, i == 0))
            
        for future in concurrent.futures.as_completed(futures):
            try:
                worktrees.append(future.result())
            except Exception:
                pass
                
    # Sort by mtime desc, but keep main at top
    main_wt = next((wt for wt in worktrees if wt.status.is_main), None)
    other_wts = sorted([wt for wt in worktrees if not wt.status.is_main], key=lambda x: x.mtime, reverse=True)
    
    result = []
    if main_wt:
        result.append(main_wt)
    result.extend(other_wts)
    
    return result
