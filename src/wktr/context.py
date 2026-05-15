from enum import Enum, auto
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from wktr.git import run_git, GitError

class ContextKind(Enum):
    IN_REPO = auto()
    REPOS_ROOT = auto()
    UNKNOWN = auto()

@dataclass
class Context:
    kind: ContextKind
    repos_root: Optional[Path] = None
    main_repo: Optional[Path] = None
    worktrees_root: Optional[Path] = None

def detect(cwd: Path) -> Context:
    cwd = cwd.resolve()
    
    try:
        common_dir_str = run_git(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=cwd)
        common_dir = Path(common_dir_str).resolve()
        
        # common_dir is usually <main_repo>/.git
        if common_dir.name == ".git":
            main_repo = common_dir.parent
        else:
            # If it's a bare repo or something else, we might need to adjust
            # But standard worktrees have common_dir pointing to the main repo's .git
            # or the bare repo dir. Let's assume standard non-bare for now.
            if common_dir.suffix == ".git":
                main_repo = common_dir.with_name(common_dir.name[:-4])
            else:
                main_repo = common_dir
                
        repos_root = main_repo.parent
        worktrees_base = repos_root / "worktrees"
        worktrees_root = worktrees_base / main_repo.name
        
        if worktrees_base.is_dir():
            return Context(
                kind=ContextKind.IN_REPO,
                repos_root=repos_root,
                main_repo=main_repo,
                worktrees_root=worktrees_root
            )
        else:
            return Context(
                kind=ContextKind.IN_REPO,
                repos_root=repos_root,
                main_repo=main_repo,
                worktrees_root=None
            )
    except GitError:
        pass
        
    if (cwd / "worktrees").is_dir():
        return Context(
            kind=ContextKind.REPOS_ROOT,
            repos_root=cwd
        )
        
    return Context(kind=ContextKind.UNKNOWN)
