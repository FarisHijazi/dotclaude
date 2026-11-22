#!bash
# shellcheck shell=sh
# Per-shell Claude Code account selection by directory (cswap-backed).
# Sourced from the dotfiles' ~/.bashrc.d/20_claude_account.sh.
#
#   inside  <work dir>/**  -> export CLAUDE_CONFIG_DIR=<cswap session
#             profile for account 2, the work account>
#   outside                -> unset it (default ~/.claude login)
#
# The profile is auth-only: the cswap fork's share-all mode symlinks
# EVERYTHING in ~/.claude except credentials and per-profile state
# (.claude.json, sessions/, ide/, statsig/, backups/), so skills, plugins,
# hooks, settings, projects/ (transcripts, --resume) and history.jsonl are
# ONE set of files for both accounts.
# Fork: https://github.com/FarisHijazi/claude-swap  (`cswap env`)
#
# Fast path: when the profile exists and isn't marked stale, export directly
# (no python on shell startup). `cswap env 2` runs only for first-time
# bootstrap or stale-credential repair; run it manually anytime to re-sync
# symlinks (e.g. after adding a global MCP server). If it prints nothing
# with rc 0, the default login already IS account 2 — no override needed.
#
# Re-evaluated on shell start and every cd (zsh chpwd / bash PROMPT_COMMAND);
# affects only this shell. The managed flag is exported so nested shells
# inheriting the var may also unset it.

# Which profile directory is the work account. Machine-specific, so it is read
# at runtime and never committed - same rule as $TCC_MAIN_REPO and the tmux
# host-color. Empty means "no work profile on this box", which the -d test
# below already handles, so a fresh machine needs no edit.
# The work tree (e.g. ~/Projects/<employer>.d) is read the same way; empty
# disables the switch entirely.
__CLAUDE_WORK_PROFILE="${CLAUDE_WORK_PROFILE:-$(cat "$HOME/.config/claude/work-profile" 2>/dev/null)}"
__CLAUDE_WORK_DIR="${CLAUDE_WORK_DIR:-$(cat "$HOME/.config/claude/work-dir" 2>/dev/null)}"
__CLAUDE_WORK_DIR="${__CLAUDE_WORK_DIR/#\~/$HOME}"
__CLAUDE_WORK_DIR="${__CLAUDE_WORK_DIR%/}"

__claude_account_eval() {
    case "$PWD/" in
    "${__CLAUDE_WORK_DIR:-/nonexistent}"/*)
        if [ -z "${CLAUDE_CONFIG_DIR:-}" ] && [ -z "${__CLAUDE_ACCT_DONE:-}" ]; then
            if [ -d "$__CLAUDE_WORK_PROFILE" ] &&
                [ ! -f "$__CLAUDE_WORK_PROFILE/.cswap-stale-credentials" ]; then
                export CLAUDE_CONFIG_DIR="$__CLAUDE_WORK_PROFILE"
            else
                eval "$(command cswap env 2)" # bootstrap/repair; chatter -> stderr
            fi
            if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
                export __CLAUDE_ACCT_MANAGED=1
            else
                # cswap env printed nothing: account 2 already is the default
                # login (or cswap failed and said so on stderr) — either way
                # don't retry on every prompt in this shell.
                __CLAUDE_ACCT_DONE=1
            fi
        fi
        ;;
    *)
        if [ -n "${__CLAUDE_ACCT_MANAGED:-}" ]; then
            unset CLAUDE_CONFIG_DIR __CLAUDE_ACCT_MANAGED
        fi
        unset __CLAUDE_ACCT_DONE
        ;;
    esac
}

# cswap manages the DEFAULT login (~/.claude). Never let it operate on the
# work profile just because this shell happens to be inside the work tree.
cswap() {
    if [ -n "${__CLAUDE_ACCT_MANAGED:-}" ]; then
        env -u CLAUDE_CONFIG_DIR cswap "$@"
    else
        command cswap "$@"
    fi
}

if [ -n "${ZSH_VERSION:-}" ]; then
    autoload -Uz add-zsh-hook
    add-zsh-hook chpwd __claude_account_eval
elif [ -n "${BASH_VERSION:-}" ]; then
    case ";${PROMPT_COMMAND:-};" in
    *";__claude_account_eval;"*) ;;
    *) PROMPT_COMMAND="__claude_account_eval${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;
    esac
fi
__claude_account_eval # evaluate the shell's starting directory
