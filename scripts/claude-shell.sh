# claude-shell.sh — Claude Code shell commands: cc, tcc, tcodex, topencode,
# tcca, tls, tmux-restore. Compatible with bash and zsh.
#
# Sourced by the dotfiles' ~/.bash_aliases when this file exists, so a box
# without dotclaude simply has no tcc. Docs: the dotfiles repo,
# docs/tmux-and-claude-sessions.md.
#
# _bidi (Arabic rendering for the tmux client) lives in ~/.bash_aliases because
# `tw` uses it too; fall back to running the command as-is without it.
command -v _bidi >/dev/null 2>&1 || _bidi() { "$@"; }

# _claude_argv — turn cc/tcc arguments into claude's argv, in CLAUDE_ARGV.
#
# ONE rule, deliberately no allowlist of value-taking flags: claude's own parser
# is the authority and no hand-kept list can track it (`-r` takes an OPTIONAL
# value, `--add-dir`/`--mcp-config` take VARIADIC ones). So the moment any
# argument looks like a flag, forward everything verbatim and let claude parse
# it; `cc`/`tcc` then behave exactly like `claude`. A pure prompt — no flags at
# all — is joined and passed after `--`, which is what keeps `tcc /resume` and
# `cc fix the bug` working without quoting.
#
# The bug this replaces: `cc` had a hardcoded `--`, so `cc -r <uuid>` ran
# `claude -- -r <uuid>` and claude read the whole thing as prompt TEXT.
_claude_argv() {
  CLAUDE_ARGV=()
  local a
  for a in "$@"; do
    case "$a" in
    -*)
      CLAUDE_ARGV=("$@")
      return 0
      ;;
    esac
  done
  [ $# -gt 0 ] && CLAUDE_ARGV=(-- "$*")
  return 0
}

cc() {
  _claude_argv "$@"
  claude-accounts -- --dangerously-skip-permissions "${CLAUDE_ARGV[@]}"
}

# `claude` sessions go through the account proxy too (claude-accounts passes
# the proxy URL in its own --settings; ~/.claude/settings.json carries none).
# `command claude` is plain Claude on this machine's own login. Management
# subcommands go straight to the binary: the router appends --chrome and
# --mcp-config, which turns `claude plugin list` into a chat prompt. Inside a
# Claude Code session (CLAUDECODE set) the Bash tool keeps the real binary.
claude() {
  if [ -n "${CLAUDECODE:-}" ]; then
    command claude "$@"
    return
  fi
  case "${1:-}" in
  agents | attach | auth | auto-mode | doctor | gateway | import | install | logs | mcp | \
    plugin | plugins | purge | respawn | rm | setup-token | stop | kill | ultrareview | \
    update | upgrade)
    command claude "$@"
    ;;
  *) claude-accounts -- "$@" ;;
  esac
}
alias ccf=claude-flow

# Convert 256-color code to hex (for VSCode integration)
_color256_to_hex() {
  local c=$1
  awk -v c="$c" 'BEGIN {
    # Standard 16 colors
    split("000000 800000 008000 808000 000080 800080 008080 c0c0c0 808080 ff0000 00ff00 ffff00 0000ff ff00ff 00ffff ffffff", std)
    if (c < 16) { print "#" std[c+1]; exit }
    # 216 color cube (16-231)
    if (c < 232) {
      c -= 16; b = c % 6; c = int(c/6); g = c % 6; r = int(c/6)
      printf "#%02x%02x%02x\n", r?r*40+55:0, g?g*40+55:0, b?b*40+55:0; exit
    }
    # Grayscale (232-255)
    v = (c - 232) * 10 + 8; printf "#%02x%02x%02x\n", v, v, v
  }'
}

# Set VSCode statusBar.background in .vscode/settings.json
_set_vscode_color() {
  local hex=$1 settings=".vscode/settings.json"
  mkdir -p .vscode
  if [ -f "$settings" ]; then
    jq --arg c "$hex" '.["workbench.colorCustomizations"]["statusBar.background"] = $c' "$settings" >"$settings.tmp" && mv "$settings.tmp" "$settings"
  else
    jq -n --arg c "$hex" '{"workbench.colorCustomizations": {"statusBar.background": $c}}' >"$settings"
  fi
}

tcc() {
  # One env switch, no extra CLI flags -- every argument belongs to `claude`:
  #   TCC_DETACH=1   (~/bin/tcc-bg, tmux-restore) create the session detached
  #                  instead of attaching, the only way this is safe from
  #                  inside tmux.

  # Nothing here is a *tcc* flag -- every argument belongs to claude; see
  # _claude_argv for why there is no allowlist of value-taking flags.
  _claude_argv "$@"

  # Mint the conversation id UP FRONT for a fresh session, so it lands in
  # claude's own argv and therefore in the resurrect snapshot. That is the whole
  # pane -> conversation mapping: tmux-restore reads the uuid back out of the
  # saved command line. Before this it guessed "newest transcript in this cwd",
  # which handed every pane in a directory the SAME uuid (~ has 56 transcripts
  # and 6 live panes) -- six claudes resuming one conversation.
  # Skipped when the caller already picks the conversation (-r/--resume/-c/
  # --continue/--session-id): claude keeps that id, so it is already in the argv.
  # The id also names this run's clean-exit marker (see _tagent), so it is
  # kept when the caller passed one: `-r <uuid>` / `--session-id <uuid>`.
  local sid_arg=() a prev="" sid=""
  local want_sid=1
  for a in "${CLAUDE_ARGV[@]}"; do
    case "$a" in
    -r | --resume | -c | --continue | --session-id | --fork-session) want_sid="" ;;
    esac
    case "$prev" in
    -r | --resume | --session-id) [[ "$a" =~ ^[0-9a-fA-F-]{36}$ ]] && sid="$a" ;;
    esac
    prev="$a"
  done
  # a fork runs under a NEW id claude picks itself: no marker to write
  case " ${CLAUDE_ARGV[*]} " in *" --fork-session "*) sid="" ;; esac
  if [ -n "$want_sid" ] && command -v uuidgen >/dev/null 2>&1; then
    sid="$(uuidgen | tr 'A-Z' 'a-z')"
    sid_arg=(--session-id "$sid")
  fi

  # Launch through claude-accounts (ftower account proxy + native Remote
  # Control, so the session shows up in cchq). Never silently fall back to a
  # direct login when the launcher is missing; TCC_PLAIN=1 opts in to plain
  # claude. TCC_MAIN_ACCOUNT picks the main account (set per machine in
  # ~/.bashrc.local). TCC_PRIVATE=1 keeps the session off claude.ai
  # (cchq only; the hub does not mirror it upstream).
  local launch=(claude)
  if [ "${TCC_PLAIN:-}" != 1 ]; then
    command -v claude-accounts >/dev/null 2>&1 || {
      echo "tcc: claude-accounts is not installed or not on PATH; refusing a direct Claude launch" >&2
      return 127
    }
    launch=(claude-accounts)
    [ -n "${TCC_MAIN_ACCOUNT:-}" ] && launch+=(--main-account "$TCC_MAIN_ACCOUNT")
    [ "${TCC_PRIVATE:-}" = 1 ] && launch+=(--private-remote-control)
    launch+=(-- --remote-control)
  fi

  TCC_SID="$sid" _tagent tcc "${launch[@]}" --dangerously-skip-permissions "${sid_arg[@]}" "${CLAUDE_ARGV[@]}"
}

# _tagent <label> <agent argv...> — the tmux half of tcc / tcodex / topencode:
# per-directory colour, `<dir>-N` starting session name (renamed after the
# Claude title by scripts/tmux-name-from-title.sh), the TCC_DETACH mode
# documented in tcc(), and the TCC_SID clean-exit marker. Only the agent argv
# differs per tool.
_tagent() {
  local label="$1"
  shift
  if [ -n "$TMUX" ] && [ -z "${TCC_DETACH:-}" ]; then
    echo "$label: refusing to run inside an existing tmux session" >&2
    return 1
  fi

  local session color hex base_name n a
  local colors="196 202 208 214 220 226 190 154 118 82 46 47 48 49 50 51 45 39 33 27 21 57 93 129 165 201 200 199 198 197"

  color=$(printf '%s' "$PWD" | cksum | awk -v c="$colors" '{split(c,a); print a[($1 % 30) + 1]}')
  hex=$(_color256_to_hex "$color")
  _set_vscode_color "$hex"

  # tmux disallows '.' and ':' in session names (it silently rewrites them to
  # '_'). Sanitize up front so every tmux call below targets the same name —
  # otherwise a dir like 'acme.d' yields session 'acme_d-1' but targets
  # 'acme.d-1', which tmux parses as pane 'd-1' ("can't find pane: d-1").
  base_name="$(basename "$PWD")"
  base_name="${base_name//[.:]/_}"
  n=1
  while tmux has-session -t "${base_name}-${n}" 2>/dev/null; do
    n=$((n + 1))
  done
  session="${base_name}-${n}"

  local cmd="tmux set-option status-style bg=colour${color};"
  for a in "$@"; do
    cmd+=" $(printf '%q' "$a")"
  done
  # Trailing statement on purpose: tmux runs this via `$SHELL -c`, and a shell
  # exec's into the LAST command of a -c list. Without this the pane process IS
  # claude, so resurrect's save strategy (`ps -ao ppid,args` on the pane pid,
  # i.e. its direct CHILDREN) records claude's stdio MCP servers instead of
  # claude -- snapshots literally read `:bun .../inbox.ts` -- and records two
  # lines, breaking the tab-separated record, when there are two children.
  # Keeping a shell in front means the pane has exactly one child: claude.
  local tmux_cmd="${cmd}; __tcc_rc=\$?; exit \$__tcc_rc"

  # Clean-exit marker for tmux-restore: removed at start, written only when the
  # agent RETURNS (rc < 128, i.e. not signal-killed). A crash, a kill, a reboot
  # or `tmux kill-server` takes this wrapper shell down with it, so the marker
  # stays absent and tmux-restore knows the conversation was cut off.
  if [ -n "${TCC_SID:-}" ]; then
    local mark
    mark="$(printf '%q' "${XDG_STATE_HOME:-$HOME/.local/state}/tcc/ended/$TCC_SID")"
    tmux_cmd="rm -f ${mark}; ${cmd}; __tcc_rc=\$?; [ \$__tcc_rc -lt 128 ] && mkdir -p \$(dirname ${mark}) && echo \$__tcc_rc >${mark}; exit \$__tcc_rc"
  fi

  if [ -n "${TCC_DETACH:-}" ]; then
    # Background mode: create it detached, print the name, leave the caller
    # (shell or tmux client) exactly where it was.
    tmux new-session -d -s "$session" -c "$PWD" \
      -e "TCC_COLOR=${color}" \
      "$tmux_cmd"
    echo "$session"
    return 0
  fi

  _bidi tmux new-session -s "$session" \
    -e "TCC_COLOR=${color}" \
    "$tmux_cmd"
  echo "exiting $label session"
  exit 0
}

# tcodex / topencode — tcc for codex and opencode, same tmux session handling
# (_tagent), each with its own skip-all-permissions flag. Arguments go to the
# agent verbatim.
tcodex() { _tagent tcodex codex --dangerously-bypass-approvals-and-sandbox "$@"; }
topencode() { _tagent topencode opencode --auto "$@"; }

# tcca — attach to a tmux session living in the current directory (by its panes'
# path, like tls: tcc sessions are renamed after their Claude title, so the name
# no longer says where they are). Skips hq-* workers and hub/* grids.
tcca() {
  local sess
  sess="$(tmux list-panes -a -F '#{session_name}	#{pane_current_path}' 2>/dev/null |
    awk -F'\t' -v d="$PWD" '$2==d && $1 !~ /^(hq-|hub\/)/ {print $1; exit}')"
  if [ -n "$sess" ]; then
    tmux attach-session -t "=$sess"
  else
    echo "No tmux session found in $PWD"
    return 1
  fi
}

# tls — like `tmux ls`, but scoped to sessions living in the current directory
# (or recursively below it). A session's location is its pane_current_path, so
# this catches tcc/tcca sessions launched here regardless of their name.
# Skips hq-* sessions (HQ workers) by default; pass --all to include them.
# Usage: tls [--all] [dir]
tls() {
  local all=0 root="$PWD" a
  for a in "$@"; do
    case "$a" in
    --all | -a) all=1 ;;
    -*)
      echo "tls: unknown flag: $a (want --all)" >&2
      return 2
      ;;
    *) root="$a" ;;
    esac
  done
  root="${root%/}"
  local names
  names="$(tmux list-panes -a -F '#{session_name}	#{pane_current_path}' 2>/dev/null |
    awk -F'\t' -v r="$root" -v all="$all" \
      '($2==r || index($2, r"/")==1) && (all || $1 !~ /^hq-/) {print $1}' | sort -u)"
  if [ -z "$names" ]; then
    echo "tls: no tmux sessions in $root or below" >&2
    return 1
  fi
  # Anchor each name so `tmux ls` lines match exactly (escape regex metachars).
  local pat
  pat="$(printf '%s\n' "$names" | sed 's/[][\\.^$*+?(){}|/]/\\&/g' | paste -sd'|' -)"
  tmux ls 2>/dev/null | grep -E "^(${pat}):"
}

# ---------------------------------------------------------------------------
# tmux-restore — bring every Claude Code conversation back after a reboot or a
# crash, each as its own fresh `tcc -r <uuid>` session. Layout is NOT restored
# (no windows, splits or plain shells): only the conversations, which is all
# that is worth having back. Runs at login on its own (install-tmux-stack.sh
# installs the LaunchAgent / systemd unit -> scripts/tmux-restore-at-login.sh).
#
# Source is the newest tmux-resurrect snapshot (continuum saves every 5 min).
# Each claude pane there carries its conversation id in its saved command line
# -- tcc mints it with --session-id -- so every pane resumes its OWN chat.
#
# Idempotent: a conversation whose id is already in a running process is
# skipped, so re-running (or running against a live server) never duplicates.
#
# Abrupt-exit nudge: tcc writes ~/.local/state/tcc/ended/<uuid> only when
# claude RETURNS by itself. No marker = it was killed (crash, kill-server, ANY
# reboot -- a deliberate one too), so the resume carries TMUX_RESTORE_NUDGE as
# its first prompt and claude picks the cut-off work back up.
#
# Skipped sessions (TMUX_RESTORE_EXCLUDE, ERE on session name):
#   hq-*   HQ routines owned by the mission-control scheduler. Hand-restoring
#          one double-runs it (2026-08-04 double-brief incident); HQ relaunches
#          them itself.
#   hub/*  the `tw` grid -- rebuild it by running `tw`.
tmux-restore() {
  local dir src f ex cnt dry=0 pick="" list=0 best bestn srcn
  # `cwd`, never `path`: in zsh `path` IS $PATH (tied array), `local path` empties it
  local cwd arg sess pd nudge res=() n_up=0 n_nudge=0 n_skip=0
  local endd="${XDG_STATE_HOME:-$HOME/.local/state}/tcc/ended"

  ex="${TMUX_RESTORE_EXCLUDE:-^(hq-|hub/)}"
  nudge="${TMUX_RESTORE_NUDGE:-[tmux-restore] This session was exited abruptly (crash, kill or reboot) and has just been resumed. If you were in the middle of something, check its state and continue; otherwise just say you are ready.}"
  while [ $# -gt 0 ]; do
    case "$1" in
    -n) dry=1 ;;
    -l) list=1 ;;
    -f)
      shift
      pick="${1:-}"
      [ -n "$pick" ] || {
        echo "tmux-restore: -f needs a snapshot" >&2
        return 2
      }
      ;;
    -h | --help)
      cat <<'USAGE'
usage: tmux-restore [-n] [-l] [-f SNAPSHOT]
  -n  dry run -- print what would come back, change nothing
  -l  list recent snapshots, newest first, with their sessions
  -f  restore a SPECIFIC snapshot (bare name or path) instead of the newest
Each claude conversation comes back as its own detached `tcc -r <uuid>`
session; ones already running are skipped. Then `tw` to see them all.
USAGE
      return 0
      ;;
    *)
      echo "tmux-restore: unknown option: $1" >&2
      return 2
      ;;
    esac
    shift
  done

  dir="${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect"
  [ -d "$dir" ] || dir="$HOME/.tmux/resurrect"
  [ -d "$dir" ] || {
    echo "tmux-restore: no resurrect snapshot dir found" >&2
    return 1
  }

  # `command ls`, NOT `ls`: .bashrc.d/70_editor_stack.sh aliases ls to eza, and
  # zsh bakes aliases into a function body at PARSE time, so the alias reaches in
  # here. eza's -t takes a value, swallowed the first filename, and left src
  # empty -- "no snapshots" against 2000+ of them. Found right after a crash.
  if [ "$list" -eq 1 ]; then
    command ls -t "$dir"/tmux_resurrect_2*.txt 2>/dev/null | head -"${TMUX_RESTORE_LIST:-15}" |
      while read -r f; do
        printf '%-34s %s  %s\n' "$(basename "$f")" \
          "$(date -r "$f" '+%F %H:%M' 2>/dev/null)" \
          "$(awk -v ex="$ex" -F'\t' '$1=="pane" && $2 !~ ex {print $2}' "$f" | sort -u | tr '\n' ' ')"
      done
    return 0
  fi

  if [ -n "$pick" ]; then
    case "$pick" in
    */*) src="$pick" ;;
    *) src="$dir/$pick" ;;
    esac
    [ -f "$src" ] || {
      echo "tmux-restore: no such snapshot: $src" >&2
      echo "              'tmux-restore -l' lists them." >&2
      return 1
    }
  else
    src=$(command ls -t "$dir"/tmux_resurrect_2*.txt 2>/dev/null | head -1)
  fi
  [ -n "$src" ] || {
    echo "tmux-restore: no snapshots in $dir" >&2
    return 1
  }

  # The newest snapshot is the WRONG one if you did not restore immediately:
  # continuum keeps saving the near-empty post-crash server over the good one.
  if [ -z "$pick" ]; then
    srcn=$(awk -v ex="$ex" -F'\t' '$1=="pane" && $2 !~ ex {print $2}' "$src" | sort -u | wc -l | tr -d ' ')
    bestn=$srcn best=""
    for f in $(command ls -t "$dir"/tmux_resurrect_2*.txt 2>/dev/null | head -"${TMUX_RESTORE_SCAN:-60}"); do
      cnt=$(awk -v ex="$ex" -F'\t' '$1=="pane" && $2 !~ ex {print $2}' "$f" | sort -u | wc -l | tr -d ' ')
      [ "$cnt" -gt "$bestn" ] && bestn=$cnt best=$f
    done
    if [ -n "$best" ]; then
      echo "tmux-restore: NOTE the newest snapshot holds $srcn session(s), but" >&2
      echo "              $(basename "$best") ($(date -r "$best" '+%F %H:%M' 2>/dev/null)) holds $bestn." >&2
      echo "              After a crash the newest file is the post-crash one. To use that older one:" >&2
      echo "                tmux-restore -f $(basename "$best")" >&2
    fi
  fi

  echo "tmux-restore: $(basename "$src")  ($(date -r "$src" '+%F %H:%M' 2>/dev/null))"
  # A tcc pane launched through claude-accounts is saved as the router's python
  # command line (claude is its grandchild); claude's args follow its `--`.
  # One line per conversation: <session> TAB <cwd> TAB <resume arg>.
  # The resume arg is the uuid after --session-id / -r / --resume, else a
  # `--resume <name>` (ps output lost its quoting, so every word up to the next
  # option is the name), else "-c" (a bare claude or bare -r). The loop pins
  # the last two to a uuid.
  while IFS="$(printf '\t')" read -r sess cwd arg; do
    # Pin a -c / name pane to a uuid NOW, the way claude itself would pick it:
    # -c = newest transcript in that cwd, a name = newest one whose /rename
    # title starts with it. Without a uuid the already-running check below is
    # blind (a second run duplicates the session) and an ambiguous name stops
    # at claude's picker, swallowing the nudge.
    if [ "${#arg}" -ne 36 ]; then
      pd="$HOME/.claude/projects/$(printf '%s' "$cwd" | sed 's/[^A-Za-z0-9]/-/g')"
      if [ "$arg" = -c ]; then
        f=$(command ls -t "$pd"/*.jsonl 2>/dev/null | head -1)
      else
        f=$(grep -ilF "\"customTitle\":\"$arg" "$pd"/*.jsonl 2>/dev/null | xargs ls -t 2>/dev/null | head -1)
      fi
      [ -n "$f" ] && arg=$(basename "$f" .jsonl)
    fi
    if [ "$arg" = -c ]; then res=(-c); else res=(-r "$arg"); fi
    if [ "${#arg}" -eq 36 ] && ps -eo args= 2>/dev/null | grep -F -- "$arg" | grep -qv 'grep'; then
      echo "  = $sess  (already running)"
      n_skip=$((n_skip + 1))
      continue
    fi
    if [ "${#arg}" -eq 36 ] && [ -f "$endd/$arg" ]; then
      echo "  + $sess  $cwd  ${res[*]}"
      [ "$dry" -eq 1 ] || (
        cd "$cwd" 2>/dev/null || cd
        TCC_DETACH=1 tcc "${res[@]}" >/dev/null
      ) || return $?
    else
      echo "  ! $sess  $cwd  ${res[*]}  (exited abruptly -> nudged)"
      [ "$dry" -eq 1 ] || (
        cd "$cwd" 2>/dev/null || cd
        TCC_DETACH=1 tcc "${res[@]}" "$nudge" >/dev/null
      ) || return $?
      n_nudge=$((n_nudge + 1))
    fi
    n_up=$((n_up + 1))
  done < <(awk -v ex="$ex" '
    BEGIN { FS = "\t" }
    $1 != "pane" || $2 ~ ex { next }
    $11 !~ /^:claude( |$)/ && $11 !~ /\/claude-account-router .* -- / { next }
    {
      path = $8; sub(/^:/, "", path)
      n = split(substr($11, 2), a, / +/); id = ""; name = ""; on = 0
      for (i = 1; i <= n; i++) {
        if (on) { if (a[i] ~ /^-/) break; name = name (name == "" ? "" : " ") a[i]; continue }
        if (a[i] == "--session-id" || a[i] == "-r" || a[i] == "--resume") {
          if (a[i + 1] ~ /^[0-9a-fA-F-]{36}$/) { id = a[i + 1]; break }
          if (a[i] != "--session-id") on = 1
        }
      }
      arg = id != "" ? id : (name != "" ? name : "-c")
      if (!seen[arg SUBSEP path]++) print $2 "\t" path "\t" arg
    }' "$src")

  [ "$dry" -eq 1 ] && return 0
  echo "tmux-restore: $n_up started ($n_nudge nudged), $n_skip already running. Run 'tw' to see them."
}
