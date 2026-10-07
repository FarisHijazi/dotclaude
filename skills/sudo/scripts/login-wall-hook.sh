#!/usr/bin/env bash
# PostToolUse hook for mcp__claude-in-chrome__* (wired in ~/.claude/settings.json).
# Claude doesn't reliably load the sudo skill before it reaches a
# login page, so this flags login walls deterministically: when a Chrome tool's
# text result or input looks like a sign-in / expired-session / MFA page, it
# injects a reminder to run the skill now. Fires once per (session, page).
# Only text blocks and the tool input are scanned, never screenshot data, so
# random base64 can't match.
input=$(cat)
text=$(jq -r '[(.tool_response | .. | objects | select(.type? == "text") | .text), (.tool_input | tostring)] | join(" ")' <<<"$input" 2>/dev/null)
[ -n "$text" ] || exit 0

pattern='/log-?in|/sign-?in|/auth([/?#]|$)|/oauth|/sso([/?#]|$)|accounts\.google\.com|signin\.aws|sign in|log in|session (has )?expired|verify it.?s you|two-factor|2-step|multi-factor|\bmfa\b|passkey'
hit=$(grep -oiE "$pattern" <<<"$text" | head -1) || exit 0
[ -n "$hit" ] || exit 0

# Once per page per session: key on the executed tab's URL when present.
session=$(jq -r '.session_id // "x"' <<<"$input")
page=$(grep -oE 'Executed on tabId: [0-9]+' <<<"$text" | head -1)
url=$(grep -oE 'https?://[^ ")]+' <<<"$text" | head -1)
mark="${TMPDIR:-/tmp}/sudo/hook-$session"
mkdir -p "${mark%/*}"
key="${page} ${url%%\?*}"
grep -qxF "$key" "$mark" 2>/dev/null && exit 0
echo "$key" >>"$mark"

msg="Possible login wall in Chrome (matched \"$hit\"). If this page wants a sign-in, an expired-session re-login, \"verify it's you\", MFA or a passkey: do NOT stop and do NOT just mention it in chat (the user may not be reading). Load the sudo skill now and run its script so the user gets a notification; their one click is full consent for the whole login. Ignore this if the page is already signed in."
jq -n --arg m "$msg" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $m}}'
