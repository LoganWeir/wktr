# AGENTS.md

## Commands

- Install/sync dev deps with `uv sync --dev`; this project uses `pyproject.toml` plus `uv.lock`, not pip requirements or Node manifests.
- Run all tests with `env GIT_CONFIG_GLOBAL=/dev/null GIT_AUTHOR_NAME='Test User' GIT_AUTHOR_EMAIL='test@example.com' GIT_COMMITTER_NAME='Test User' GIT_COMMITTER_EMAIL='test@example.com' uv run pytest` to keep temp Git repos from inheriting global hooks/config.
- Run focused tests with the same env prefix, e.g. `... uv run pytest tests/test_naming.py::test_branch_to_dirname`.
- Install the CLI locally as a uv tool with `uv tool install .`; the console script is `wktr = "wktr.cli:main"`.

## Architecture Notes

- Source package is `src/wktr`; tests are in `tests`; build backend is Hatchling and package data includes `src/wktr/shell/*.zsh`.
- `src/wktr/cli.py` is the command dispatcher; `src/wktr/actions.py` owns command behavior; `src/wktr/context.py` detects repo/worktree context; `src/wktr/worktree.py` shells out to `git worktree`.
- `wktr` assumes repos live under a repos root with sibling worktrees at `<repos_root>/worktrees/<repo-name>/<branch-dir>`.
- Context detection treats any cwd with a `worktrees/` child as a repos root; inside a Git repo, it derives the main repo from `git rev-parse --git-common-dir`.

## CLI / Shell Wrapper Gotchas

- `cli.main()` redirects `sys.stdout` to `sys.stderr`; stdout fd 1 is reserved for shell-consumed values.
- Use `os.write(1, ...)` only for values the shell wrapper should capture, currently cd targets and `shell-init`; keep diagnostics, tables, prompts, and errors on stderr.
- The zsh wrapper runs `target=$(WKTR_SHELL=1 command wktr "$@")` and `cd`s only when stdout is a non-empty existing directory.
- Interactive UI reads `/dev/tty` directly and has fallback stdin prompts; avoid tests that require a real terminal unless explicitly isolated.

## Testing Notes

- Worktree tests create temporary Git repos and commits, so they need usable Git identity and no interfering global Git hooks.
- There is no configured lint/typecheck/formatter command in the repo; pytest is the only configured verification in `pyproject.toml`.
