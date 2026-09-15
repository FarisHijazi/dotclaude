End EVERY response with exactly ONE outcome emoji as the very last characters — same line as the
final sentence, three spaces before it, nothing after it. So: `...all set.   ✅`

cc-notify's Stop hook reads this trailing emoji for the notification + terminal tab. Never omit it.

Pick the FIRST that applies (top = strongest signal):

| | |
|---|---|
| 🚨 | an accident/disaster happened (e.g. deleted a prod DB) — emergency, overrides everything |
| 💯 | every concrete task completed, nothing left to do |
| ✅ | a concrete task completed successfully |
| ❌ | a concrete task failed or could not be completed |
| 🚫 | BLOCKED: can't proceed until something is resolved |
| 🙋 | WAITING on your instructions / a decision |
| 👍 | good news / positive result (no specific task) |
| 👎 | bad news / negative result (no specific task) |
| 🏃 | WORK to be done: remaining steps or a proposed plan awaiting go-ahead |
| ℹ️ | JUST INFO: answered with information, nothing actionable (weakest) |
| 🥱 | NOTHING happened — a loop/poll/monitor tick that found nothing new. Updates the tab but fires NO notification banner, so a per-minute poll doesn't ping you every minute. ONLY inside a running loop/poll, never a normal turn. |

IMPORTANT: these emojis (🚨 💯 ✅ ❌ 🚫 🙋 👍 👎 🏃 ℹ️ 🥱) may appear ONLY as that single trailing
token — never inline, in bullets, or as a done-marker on a heading, which makes the outcome look like
it repeats. To mark something done mid-message use plain text or a non-token glyph like ✓.
