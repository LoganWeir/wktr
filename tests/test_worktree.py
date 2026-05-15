import subprocess
from pathlib import Path
from wktr.worktree import parse_worktree_list, get_worktrees

def test_parse_worktree_list(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_dir, check=True)
    
    wt_dicts = parse_worktree_list(repo_dir)
    assert len(wt_dicts) == 1
    assert wt_dicts[0]["path"] == repo_dir
    assert "branch" in wt_dicts[0]
    
    # Add a worktree
    wt_dir = tmp_path / "wt1"
    subprocess.run(["git", "worktree", "add", "-b", "feature", str(wt_dir)], cwd=repo_dir, check=True)
    
    wt_dicts = parse_worktree_list(repo_dir)
    assert len(wt_dicts) == 2
    assert wt_dicts[0]["path"] == repo_dir
    assert wt_dicts[1]["path"] == wt_dir
    assert wt_dicts[1]["branch"] == "feature"

def test_get_worktrees(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_dir, check=True)
    
    wts = get_worktrees(repo_dir)
    assert len(wts) == 1
    assert wts[0].status.is_main
    assert wts[0].status.is_clean
