---
title: Tmux Codex CLI Initialization
name: tmux-codex-initialization
version: 1.0
description: Proper initialization sequence for Codex CLI in tmux sessions to avoid hangs
---

# Tmux Codex CLI Initialization

## Problem
Codex CLI sessions launched via tmux frequently hang in "launching" state because:
1. MCP servers take 10-20 seconds to initialize
2. Prompt sent before MCP ready is lost or ignored
3. Default 2-second supervisor wait is insufficient

## Prerequisites
- Tmux session created but Codex not yet launched
- MCP server will auto-start with Codex

## Steps

1. **Create tmux session**
   ```bash
   tmux new-session -d -s <session-name> -c /repo/path
   ```

2. **Launch vanilla Codex with the correct autonomy settings**
   ```bash
   tmux send-keys -t <session-name> "export TERM=xterm-256color && codex --yolo" C-m
   ```
   Use vanilla Codex as the default CLI surface in this skill stack.

3. **WAIT for MCP initialization (CRITICAL)**
   ```bash
   sleep 18  # Use 15-20s minimum; 18s is a good default gate before readiness checks
   ```

4. **Dismiss Codex startup prompts before sending the task**
   ```bash
   tmux capture-pane -pt <session-name> -S -120
   # If Codex asks "Do you trust the contents of this directory?", send:
   tmux send-keys -t <session-name> "1" C-m
   # If the pane still says "Press enter to continue" before the Codex UI becomes responsive, send:
   tmux send-keys -t <session-name> C-m
   ```

5. **Verify Codex is responsive**
   ```bash
   tmux capture-pane -pt <session-name> -S -120
   # Look for Codex UI text, model/context info, MCP output, or "(esc to interrupt)"
   ```

6. **Send task prompt only after verification**
   ```bash
   tmux send-keys -t <session-name> "<your prompt here>" C-m
   ```

7. **Then monitor/review through the normal pipeline**
   - monitor pane output every ~30 seconds
   - nudge only if output is unchanged and work is unfinished
   - for substantial jobs, run `/review unstaged changes`
   - require `<< Code review finished >>` then a fix/rerun pass

## Verification Checklist
- [ ] Pane shows "gpt-X.X" model indicator
- [ ] Pane shows context % (not "100% left" indefinitely)
- [ ] Codex responds to simple input (try "help" first)

## Troubleshooting

### "100% left" with no response
- Codex not receiving input via send-keys
- Try: `tmux respawn-pane -t <session> -k` and restart
- Or use interactive attach: `tmux attach -t <session>` and type manually

### Session stuck in "launching" after 20+ polls
- Kill and restart with longer MCP wait
- Check MCP server logs: `~/.codex/mcp-*.log`

### Works interactively but not via supervisor
- Supervisor's send-keys may need `-l` flag for literal strings
- Or terminal mode issue - ensure TERM=xterm-256color

## Pitfalls
- **NEVER** send prompt immediately after codex launch
- **ALWAYS** verify MCP initialized before sending work
- Don't trust "unchanged_polls" alone - check actual pane content
