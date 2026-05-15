import sys
import os
import argparse
from pathlib import Path
from wktr import __version__
from wktr.context import detect
from wktr.actions import (
    cmd_pick, cmd_add, cmd_rm, cmd_ls, cmd_init, cmd_shell_init
)

def main() -> int:
    # Enforce stdout/stderr discipline
    # Save original stdout fd just in case, but we use os.write(1, ...) in actions.py
    sys.stdout = sys.stderr
    
    parser = argparse.ArgumentParser(description="Manage git worktrees")
    parser.add_argument("--version", action="version", version=__version__)
    
    subparsers = parser.add_subparsers(dest="command")
    
    # add
    add_parser = subparsers.add_parser("add", help="Add a new worktree")
    add_parser.add_argument("-b", "--branch", action="store_true", help="Create a new branch")
    add_parser.add_argument("name", help="Branch name")
    
    # rm
    rm_parser = subparsers.add_parser("rm", help="Remove a worktree")
    rm_parser.add_argument("-f", "--force", action="store_true", help="Force removal")
    rm_parser.add_argument("target", help="Branch name or directory name")
    
    # ls
    subparsers.add_parser("ls", help="List worktrees (scriptable)")
    
    # init
    subparsers.add_parser("init", help="Initialize worktrees directory")
    
    # shell-init
    subparsers.add_parser("shell-init", help="Print shell initialization script")
    
    args = parser.parse_args()
    
    if args.command == "shell-init":
        return cmd_shell_init()
        
    cwd = Path.cwd()
    ctx = detect(cwd)
    
    if args.command == "init":
        return cmd_init(ctx, cwd)
        
    if args.command == "ls":
        return cmd_ls(ctx)
        
    if args.command == "add":
        if not os.environ.get("WKTR_SHELL"):
            sys.stderr.write("Warning: WKTR_SHELL not set. The tool cannot change your directory. Consider adding `eval \"$(wktr shell-init)\"` to your shell config.\n")
        return cmd_add(ctx, args.name, args.branch)
        
    if args.command == "rm":
        return cmd_rm(ctx, args.target, args.force)
        
    if args.command is None:
        if not os.environ.get("WKTR_SHELL"):
            sys.stderr.write("Warning: WKTR_SHELL not set. The tool cannot change your directory. Consider adding `eval \"$(wktr shell-init)\"` to your shell config.\n")
        return cmd_pick(ctx)
        
    return 2
