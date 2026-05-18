import subprocess

from wktr.actions import cmd_add, cmd_rm
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


def test_add_creates_tracking_worktree_for_remote_only_branch(tmp_path):
    repos_root = tmp_path / "repos"
    origin_dir = tmp_path / "origin.git"
    source_dir = tmp_path / "source"
    repo_dir = repos_root / "repo"
    branch = "fix/kit-validation-spot-registered"
    worktree_dir = repos_root / "worktrees" / "repo" / "fix-kit-validation-spot-registered"

    repos_root.mkdir()
    source_dir.mkdir()
    subprocess.run(["git", "init", "--bare", str(origin_dir)], check=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=source_dir, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=source_dir, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(origin_dir)], cwd=source_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=source_dir, check=True)
    subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=origin_dir, check=True)
    subprocess.run(["git", "switch", "-c", branch], cwd=source_dir, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "branch commit"], cwd=source_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], cwd=source_dir, check=True)
    subprocess.run(["git", "clone", str(origin_dir), str(repo_dir)], check=True)
    (repos_root / "worktrees").mkdir()

    ctx = detect(repo_dir)

    assert cmd_add(ctx, branch, create_branch=False) == 0
    assert worktree_dir.exists()

    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=worktree_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=worktree_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert current_branch == branch
    assert upstream == f"origin/{branch}"
