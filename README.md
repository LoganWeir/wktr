# wktr

A small CLI for creating, listing, switching to, and removing git worktrees without remembering the `git worktree` commands or where each worktree lives.

## Installation

```bash
uv tool install .
```

## Shell Setup

To allow `wktr` to change your directory, add this to your `.zshrc`:

```bash
eval "$(wktr shell-init)"
```

Without the shell wrapper, `wktr` can still run, but it cannot change the current directory of your shell. The wrapper captures the selected path from `wktr` and performs the `cd` for you.

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

Run `wktr init` from the repos directory to create `worktrees/` if it does not exist yet.

New worktrees are created under:

```text
<repos-root>/worktrees/<repo-name>/<branch-dir>/
```

The `<branch-dir>` is generated automatically from the branch name. Slashes and filesystem-unsafe characters are replaced with `-`, so `feature/foo` becomes `feature-foo`. If a generated directory name would collide with a different existing branch, `wktr` appends a short hash suffix.

## Usage

From the repos directory, `wktr` shows the repositories that have matching folders under that root. Select a repo by number, then select one of its worktrees:

```bash
cd ~/Documents/repos
wktr
```

From inside a repo or one of its worktrees, `wktr` skips repo selection and shows that repo's worktrees directly:

```bash
cd ~/Documents/repos/my-repo
wktr
```

In the interactive picker:

- `<number><enter>` changes into that worktree.
- `<number>d<enter>` deletes that worktree.
- `d<enter>` deletes the currently highlighted worktree.
- `j` / `k` or arrow keys move the highlight.
- `q`, `Esc`, or `Ctrl-C` exits.

Worktree lists show branch name, directory name, last commit time, and status. The main repo is shown but cannot be deleted.

Create a worktree for an existing branch:

```bash
cd ~/Documents/repos/my-repo
wktr add feature/foo
```

Create a new branch and worktree from the current HEAD:

```bash
wktr add -b feature/foo
```

Both `add` forms print the new worktree path for the shell wrapper, so your shell changes into the new worktree automatically.

## Commands

- `wktr` — Interactive picker. From a repos root, pick a repo first; from inside a repo, pick a worktree directly.
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
