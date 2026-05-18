---
name: Always review and test changes before deploying
description: After editing code, grep for stale references to removed variables/functions before rebuilding — don't leave dead code paths that cause runtime errors
type: feedback
---

When removing or renaming a variable/function, search the entire file for ALL references before considering the change done. Don't just delete the declaration and update one call site — there may be other references that will cause `NameError` at runtime.

**Why:** On 2026-05-11, removed `WHISPER_API_URL` and `WHISPER_API_KEY` variables from bot.py but left two lines in `transcribe_voice()` still referencing them (`whisper_url = WHISPER_API_URL`, `whisper_key = WHISPER_API_KEY`). The bot deployed, voice notes hit `NameError`, and the bot told users their voice messages were "unclear" instead of transcribing them. This shipped to production and was only caught when the user tested it manually.

**How to apply:** After any rename/removal, run `grep -n 'OLD_NAME' file.py` before committing. For deployed services (Docker containers), always check logs after rebuild (`docker compose logs bot --tail=20`) to verify there are no runtime errors — type checking and syntax won't catch `NameError` on variables that are only reached at runtime. Don't claim "done" until you've seen the new code path actually execute successfully in logs.
