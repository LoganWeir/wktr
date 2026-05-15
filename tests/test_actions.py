import subprocess

from wktr.actions import cmd_rm
from wktr.context import detect


def test_rm_removes_worktree_from_main_repo(tmp_path):
    repos_root = tmp_path / "repos"
    repo_dir = repos_root / "repo"
    worktree_dir = repos_root / "worktrees" / "repo" / "feature"
    repo_dir.mkdir(parents=True)
    worktree_dir.parent.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(worktree_dir)],
        cwd=repo_dir,
        check=True,
    )

    ctx = detect(repo_dir)

    assert cmd_rm(ctx, "feature", force=False) == 0
    assert not worktree_dir.exists()

    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert str(worktree_dir) not in worktrees
