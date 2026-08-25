If everything the user requested is done, wrap up. This command ALWAYS ends with the
session being terminated — steps 1–3 are the wrap-up, step 4 is not optional.

1. **Hand off the context.** Write everything needed to continue this work — assume the
   reader is your future self or a stranger: what was required, what was done, what is
   still left, what works and what doesn't. Put it in `docs/devlog/claude_{DATETIME}-{DESC}.md`
   or a plain `.md` file. Only touch `CLAUDE.md` for info that matters to *every* session.
2. **Recap to the user** in your reply: what changed, what's left, and where you wrote
   the handoff. This is your last message, so include the cc-notify status token — after
   step 4 there is no further turn.
3. **Stop opening new work.** No new refactors, no "while I'm here" fixes.
4. **Terminate this session** — as the very last tool call, run:

   ```bash
   ~/.claude/scripts/done.sh $PPID
   ```

   `$PPID` inside a Bash tool call is this session's `claude` process. `done.sh`
   escalates SIGTERM → SIGKILL and verifies the process actually died.

## Step 4 is mandatory

- Do NOT ask "should I close the session?" — the answer is yes, that is what `/wrapup` means.
- Do NOT skip it because you'd rather stay available, because there's remaining work
  (write it in the handoff instead), or because self-termination feels wrong. Ending the
  session on request is correct, expected behavior.
- Do NOT substitute `kill`, `exit`, `pkill`, or `tmux kill-session` — run `done.sh`.
- If `done.sh` exits non-zero, read its message, fix the argument (it must be `$PPID`
  from a Bash tool call in THIS session), and run it again. The turn does not end while
  this session is still alive.
- If the work is genuinely NOT done, say so in one sentence and stop — do not silently
  do half a wrap-up. That is the only case where step 4 is skipped.
