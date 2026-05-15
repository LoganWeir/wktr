from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class Repo:
    name: str
    path: Path
    worktrees_dir: Path

def discover_repos(repos_root: Path) -> List[Repo]:
    """
    Discover repositories in repos_root that have a corresponding worktrees directory.
    """
    repos = []
    worktrees_base = repos_root / "worktrees"
    
    if not worktrees_base.is_dir():
        return repos
        
    for wt_dir in worktrees_base.iterdir():
        if not wt_dir.is_dir():
            continue
            
        repo_name = wt_dir.name
        repo_path = repos_root / repo_name
        
        if repo_path.is_dir() and (repo_path / ".git").exists():
            repos.append(Repo(
                name=repo_name,
                path=repo_path,
                worktrees_dir=wt_dir
            ))
            
    return sorted(repos, key=lambda r: r.name)
