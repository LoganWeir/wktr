import subprocess
from pathlib import Path
from wktr.context import detect, ContextKind

def test_detect_in_repo(tmp_path):
    repos_root = tmp_path / "repos"
    repos_root.mkdir()
    
    repo_dir = repos_root / "my-repo"
    repo_dir.mkdir()
    
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    
    ctx = detect(repo_dir)
    assert ctx.kind == ContextKind.IN_REPO
    assert ctx.repos_root == repos_root
    assert ctx.main_repo == repo_dir
    assert ctx.worktrees_root is None
    
    worktrees_dir = repos_root / "worktrees"
    worktrees_dir.mkdir()
    
    ctx = detect(repo_dir)
    assert ctx.kind == ContextKind.IN_REPO
    assert ctx.repos_root == repos_root
    assert ctx.main_repo == repo_dir
    assert ctx.worktrees_root == worktrees_dir / "my-repo"

def test_detect_repos_root(tmp_path):
    repos_root = tmp_path / "repos"
    repos_root.mkdir()
    
    worktrees_dir = repos_root / "worktrees"
    worktrees_dir.mkdir()
    
    ctx = detect(repos_root)
    assert ctx.kind == ContextKind.REPOS_ROOT
    assert ctx.repos_root == repos_root

def test_detect_unknown(tmp_path):
    ctx = detect(tmp_path)
    assert ctx.kind == ContextKind.UNKNOWN
