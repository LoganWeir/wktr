# wktr

A tool to help manage git worktrees.

## Installation

```bash
uv tool install .
```

## Shell Setup

To allow `wktr` to change your directory, add this to your `.zshrc`:

```bash
eval "$(wktr shell-init)"
```

## Directory Layout

`wktr` expects a layout where your repositories are in a base directory, and worktrees are stored in a sibling `worktrees/` directory.

```
~/Documents/repos/
├── worktrees/
│   └── my-repo/
│       ├── feature-foo/
│       └── bugfix-bar/
└── my-repo/
    └── .git/
```

## Commands

- `wktr` — Interactive picker. Select a worktree to `cd` into it, or press `d` to delete it.
- `wktr add <branch>` — Create a worktree from an existing branch and `cd` into it.
- `wktr add -b <branch>` — Create a new branch and worktree from current HEAD and `cd` into it.
- `wktr init` — Create the `worktrees/` directory in the current directory.
- `wktr ls` — Non-interactive list of worktrees (tab-separated).
- `wktr rm <branch|dirname>` — Non-interactive delete (use `--force` to bypass checks).
- `wktr shell-init` — Print the shell initialization script.

## Manual Smoke Test

1. Create a base directory: `mkdir -p /tmp/wktr-test && cd /tmp/wktr-test`
2. Initialize worktrees: `wktr init`
3. Create a repo: `mkdir repo && cd repo && git init && git commit --allow-empty -m "initial"`
4. Add a worktree: `wktr add -b feature-1`
5. List worktrees: `wktr ls`
6. Interactive picker: `wktr`

## Troubleshooting

- **Tool doesn't change directory**: Ensure you have added `eval "$(wktr shell-init)"` to your shell config.
- **Terminal weirdness**: If the terminal gets messed up, run `reset`.
