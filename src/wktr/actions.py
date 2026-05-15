import os
import sys
from pathlib import Path
from typing import Optional
from wktr.context import Context, ContextKind
from wktr.git import run_git, GitError, check_ref_format
from wktr.worktree import get_worktrees, Worktree
from wktr.repo import discover_repos
from wktr.naming import branch_to_dirname
from wktr.ui import pick_worktree, pick_repo, render_table

def emit_cd_target(path: Path):
    """Emit the target path to stdout for the shell wrapper to cd into."""
    os.write(1, str(path).encode('utf-8') + b'\n')

def cmd_shell_init():
    script = """wktr() {
  local target; target=$(WKTR_SHELL=1 command wktr "$@"); local ec=$?
  [[ $ec -eq 0 && -n "$target" && -d "$target" ]] && cd "$target"
  return $ec
}"""
    # Write to stderr so it can be eval'd if they run `wktr shell-init` directly?
    # Wait, if they run `eval "$(wktr shell-init)"`, it needs to go to stdout.
    # But we override stdout to stderr in cli.py.
    # We should use os.write(1, ...) for shell-init too.
    os.write(1, script.encode('utf-8') + b'\n')
    return 0

def cmd_init(ctx: Context, cwd: Path):
    if ctx.kind == ContextKind.REPOS_ROOT:
        sys.stderr.write("Already in a repos root.\n")
        return 0
        
    worktrees_dir = cwd / "worktrees"
    worktrees_dir.mkdir(exist_ok=True)
    sys.stderr.write(f"Initialized worktrees root at {worktrees_dir}\n")
    return 0

def cmd_ls(ctx: Context):
    if ctx.kind != ContextKind.IN_REPO:
        sys.stderr.write("Not in a repository.\n")
        return 3
        
    worktrees = get_worktrees(ctx.main_repo)
    for wt in worktrees:
        mtime_str = str(wt.mtime)
        status = "main" if wt.status.is_main else "worktree"
        sys.stderr.write(f"{wt.branch}\t{wt.path.name}\t{mtime_str}\t{status}\n")
    return 0

def cmd_add(ctx: Context, branch: str, create_branch: bool):
    if ctx.kind != ContextKind.IN_REPO:
        sys.stderr.write("Not in a repository.\n")
        return 3
        
    if not ctx.worktrees_root:
        sys.stderr.write(f"No worktrees directory found for this repo. Run `wktr init` in {ctx.repos_root}\n")
        return 3
        
    if create_branch and not check_ref_format(branch):
        sys.stderr.write(f"Invalid branch name: {branch}\n")
        return 2
        
    ctx.worktrees_root.mkdir(parents=True, exist_ok=True)
    
    # Get existing worktrees to check for collisions
    worktrees = get_worktrees(ctx.main_repo)
    existing_branches = {wt.path.name: wt.branch for wt in worktrees if wt.branch}
    
    dirname = branch_to_dirname(branch, ctx.worktrees_root, existing_branches)
    target_path = ctx.worktrees_root / dirname
    
    try:
        if create_branch:
            run_git(["worktree", "add", "-b", branch, str(target_path)], cwd=ctx.main_repo)
        else:
            run_git(["worktree", "add", str(target_path), branch], cwd=ctx.main_repo)
            
        sys.stderr.write(f"Created worktree at {target_path}\n")
        emit_cd_target(target_path)
        return 0
    except GitError as e:
        sys.stderr.write(f"Failed to create worktree: {e}\n")
        return 1

def _do_rm(wt: Worktree, force: bool) -> int:
    if wt.status.is_main:
        sys.stderr.write("Cannot delete main worktree.\n")
        return 1
        
    if wt.status.is_locked and not force:
        sys.stderr.write("Worktree is locked. Use --force to delete.\n")
        return 1
        
    if not wt.status.is_clean and not force:
        sys.stderr.write(f"Worktree has uncommitted changes. Type the dirname ({wt.path.name}) to confirm: ")
        sys.stderr.flush()
        try:
            ans = input().strip()
            if ans != wt.path.name:
                sys.stderr.write("Aborted.\n")
                return 1
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write("\nAborted.\n")
            return 1
            
    try:
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(wt.path))
        run_git(args, cwd=wt.path.parent)
        sys.stderr.write(f"Removed worktree {wt.path.name}\n")
        return 0
    except GitError as e:
        sys.stderr.write(f"Failed to remove worktree: {e}\n")
        return 1

def cmd_rm(ctx: Context, target: str, force: bool):
    if ctx.kind != ContextKind.IN_REPO:
        sys.stderr.write("Not in a repository.\n")
        return 3
        
    worktrees = get_worktrees(ctx.main_repo)
    
    # Find by branch or dirname
    wt_to_rm = None
    for wt in worktrees:
        if wt.branch == target or wt.path.name == target:
            wt_to_rm = wt
            break
            
    if not wt_to_rm:
        sys.stderr.write(f"Worktree not found: {target}\n")
        return 1
        
    return _do_rm(wt_to_rm, force)

def cmd_pick(ctx: Context):
    if ctx.kind == ContextKind.UNKNOWN:
        sys.stderr.write("Not in a repository or repos root.\n")
        return 3
        
    if ctx.kind == ContextKind.REPOS_ROOT:
        repos = discover_repos(ctx.repos_root)
        if not repos:
            sys.stderr.write("No repositories found with worktrees.\n")
            return 1
            
        repo_path = pick_repo(repos)
        if not repo_path:
            return 130
            
        # Re-detect context in the chosen repo
        from wktr.context import detect
        ctx = detect(repo_path)
        
    if ctx.kind == ContextKind.IN_REPO:
        worktrees = get_worktrees(ctx.main_repo)
        if not worktrees:
            sys.stderr.write("No worktrees found.\n")
            return 1
            
        wt, action = pick_worktree(worktrees)
        if not wt:
            return 130
            
        if action == 'cd':
            emit_cd_target(wt.path)
            return 0
        elif action == 'rm':
            return _do_rm(wt, force=False)
            
    return 1
