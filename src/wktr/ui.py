import os
import sys
import tty
import termios
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from wktr.worktree import Worktree

def is_color_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True

def format_status(wt: Worktree) -> str:
    if wt.status.is_main:
        return "(main)"
    if wt.status.is_gone:
        return "[gone]"
    
    parts = []
    if wt.status.is_locked:
        parts.append("[L]")
        
    if wt.status.is_detached:
        parts.append(f"(detached @ {wt.status.detached_at})")
    else:
        if wt.status.is_clean:
            parts.append("clean")
        else:
            parts.append("dirty")
            
        ab = []
        if wt.status.ahead:
            ab.append(f"↑{wt.status.ahead}")
        if wt.status.behind:
            ab.append(f"↓{wt.status.behind}")
        if ab:
            parts.append("".join(ab))
        elif wt.status.ahead is not None and wt.status.behind is not None:
            # Both 0
            pass
        elif not wt.status.is_detached and wt.branch:
            # No upstream
            parts.append("-")
            
    return " ".join(parts)

def render_table(worktrees: List[Worktree], selected_idx: int = -1, highlight: bool = False) -> str:
    if not worktrees:
        return "No worktrees found."
        
    # Calculate column widths
    idx_w = len(str(len(worktrees)))
    branch_w = max((len(wt.branch) if wt.branch else 10 for wt in worktrees), default=10)
    dir_w = max((len(wt.path.name) for wt in worktrees), default=10)
    
    lines = []
    header = f"{'#':>{idx_w}} | {'branch':<{branch_w}} | {'dir':<{dir_w}} | {'mtime':<16} | status"
    lines.append(header)
    lines.append("-" * len(header))
    
    color = is_color_enabled()
    
    for i, wt in enumerate(worktrees):
        idx_str = str(i + 1)
        branch_str = wt.branch or "(detached)"
        dir_str = wt.path.name
        mtime_str = datetime.fromtimestamp(wt.mtime).strftime("%Y-%m-%d %H:%M") if wt.mtime else "unknown"
        status_str = format_status(wt)
        
        line = f"{idx_str:>{idx_w}} | {branch_str:<{branch_w}} | {dir_str:<{dir_w}} | {mtime_str:<16} | {status_str}"
        
        if highlight and i == selected_idx:
            if color:
                line = f"\033[7m{line}\033[0m"
            else:
                line = f"> {line}"
        elif not highlight and not color:
            line = f"  {line}"
            
        lines.append(line)
        
    return "\n".join(lines)

def getch(fd: int) -> str:
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1).decode('utf-8')
        if ch == '\x1b':
            # Read escape sequence
            ch += os.read(fd, 2).decode('utf-8')
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def pick_worktree(worktrees: List[Worktree]) -> Tuple[Optional[Worktree], Optional[str]]:
    """
    Interactive picker. Returns (selected_worktree, action)
    action can be 'cd' or 'rm'
    """
    if not worktrees:
        return None, None
        
    try:
        fd = os.open('/dev/tty', os.O_RDWR)
    except OSError:
        # Fallback to simple input
        sys.stderr.write(render_table(worktrees) + "\n")
        sys.stderr.write("Select index: ")
        sys.stderr.flush()
        try:
            ans = input().strip()
            if not ans:
                return None, None
            if ans.endswith('d'):
                idx = int(ans[:-1]) - 1
                return worktrees[idx], 'rm'
            else:
                idx = int(ans) - 1
                return worktrees[idx], 'cd'
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            return None, None
            
    selected_idx = 0
    buf = ""
    
    try:
        while True:
            # Clear screen and render
            os.write(fd, b"\033[2J\033[H")
            table = render_table(worktrees, selected_idx, highlight=True)
            os.write(fd, table.encode('utf-8'))
            os.write(fd, b"\n\n")
            
            prompt = f"Command (e.g. 12, 3d, d, q) [{buf}]: "
            os.write(fd, prompt.encode('utf-8'))
            
            ch = getch(fd)
            
            if ch in ('q', '\x03', '\x1b'): # q, Ctrl-C, Esc
                return None, None
            elif ch == '\r': # Enter
                if buf.endswith('d'):
                    if len(buf) > 1:
                        try:
                            idx = int(buf[:-1]) - 1
                            if 0 <= idx < len(worktrees):
                                return worktrees[idx], 'rm'
                        except ValueError:
                            pass
                    else:
                        return worktrees[selected_idx], 'rm'
                elif buf:
                    try:
                        idx = int(buf) - 1
                        if 0 <= idx < len(worktrees):
                            return worktrees[idx], 'cd'
                    except ValueError:
                        pass
                else:
                    return worktrees[selected_idx], 'cd'
                buf = ""
            elif ch == '\x7f': # Backspace
                buf = buf[:-1]
            elif ch in ('j', '\x1b[B'): # Down
                selected_idx = min(len(worktrees) - 1, selected_idx + 1)
                buf = ""
            elif ch in ('k', '\x1b[A'): # Up
                selected_idx = max(0, selected_idx - 1)
                buf = ""
            elif ch.isalnum():
                buf += ch
    finally:
        os.write(fd, b"\033[2J\033[H")
        os.close(fd)

def pick_repo(repos: List) -> Optional[Path]:
    """Simple picker for repos."""
    if not repos:
        return None
        
    try:
        fd = os.open('/dev/tty', os.O_RDWR)
    except OSError:
        for i, r in enumerate(repos):
            sys.stderr.write(f"{i+1}. {r.name}\n")
        sys.stderr.write("Select repo: ")
        sys.stderr.flush()
        try:
            ans = input().strip()
            idx = int(ans) - 1
            return repos[idx].path
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            return None
            
    selected_idx = 0
    
    try:
        while True:
            os.write(fd, b"\033[2J\033[H")
            os.write(fd, b"Select repository:\n\n")
            
            for i, r in enumerate(repos):
                prefix = "> " if i == selected_idx else "  "
                if is_color_enabled() and i == selected_idx:
                    line = f"\033[7m{prefix}{r.name}\033[0m\n"
                else:
                    line = f"{prefix}{r.name}\n"
                os.write(fd, line.encode('utf-8'))
                
            ch = getch(fd)
            
            if ch in ('q', '\x03', '\x1b'):
                return None
            elif ch == '\r':
                return repos[selected_idx].path
            elif ch in ('j', '\x1b[B'):
                selected_idx = min(len(repos) - 1, selected_idx + 1)
            elif ch in ('k', '\x1b[A'):
                selected_idx = max(0, selected_idx - 1)
    finally:
        os.write(fd, b"\033[2J\033[H")
        os.close(fd)
