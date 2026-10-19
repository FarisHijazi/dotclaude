---
name: omni
description: Search the user's own personal and work data — Gmail (all their accounts), Google Drive, WhatsApp, iMessage, Basecamp posts/comments/to-dos and Campfire chats — with the `omni` CLI (hybrid keyword + semantic, Arabic and English). Use this whenever the user asks about something they said, received, sent, wrote, agreed or were told, e.g. "what did X say about Y", "find the email/message/doc where…", "when did I…", "who sent me…", "what's the status of <work topic> on Basecamp", "do I have a contract/invoice/receipt for…", or wants context from their own chats, inbox or files — even if they don't say "omni" or "search". Prefer it over Gmail/Drive MCPs or browsing for anything already indexed, because it covers every account and source in one query.
---

# omni — search the user's own data

One Meilisearch index on the homelab holds every message, email, doc and Basecamp
post the user has, refreshed hourly. The `omni` CLI queries it. Results are the user's
private data: read them freely to answer, but don't copy them anywhere outside this
conversation (no web tools, issues or third-party services) unless the user asks.

## Commands

```bash
omni search "<query>" [-s SOURCE]... [-a ACCOUNT]... [--since YYYY-MM-DD] [--until YYYY-MM-DD] \
            [-n 10] [--recent] [--ratio 0.6] [--json]
omni get <id> [-c N] [--json]     # whole document, or a chat message with N messages either side
omni status                        # doc counts per source/account, queue, last-run cursors
```

- `SOURCE`: `gmail`, `gdrive`, `whatsapp`, `imessage`, `basecamp` (Campfire chat lines are
  `basecamp` too, with kind `chat`).
- `ACCOUNT`: as shown in `[source/account]` on each hit. Gmail/Drive accounts are gws profile
  names, Basecamp is the workspace, WhatsApp is the user's phone number, iMessage is `mac`.
  Run `omni status` once to see the real list instead of guessing.
- Each hit prints: title, **document id**, `[source/account]`, date, author, score, a cropped
  snippet, and for chats the 2 messages before and after (dimmed). The snippet is ~60 words;
  run `omni get <id>` to read the full email/doc, or `omni get <id> -c 10` for a wider chat window.

## How to search well

- **Write the query the way the content is written.** Most chats and Basecamp are Arabic,
  much email is English. When unsure, run both: `omni search "عقد الإيجار"` and
  `omni search "lease contract"`. Semantic search bridges some of the gap, not all of it.
- **Names and exact phrases** (a person, an invoice number, a project code): lower `--ratio`
  to 0.2–0.3 so keyword matching dominates. **Fuzzy topics**: keep the default 0.6 or raise it.
- **Narrow early**: `-s`, `-a`, `--since/--until` cut noise far better than a longer query.
- **"Latest / most recent / last time"**: add `--recent` (sorts by date instead of relevance).
- Try 2–4 phrasings before concluding something isn't there, then say what you searched.
- **Once you have the literal answer, sweep for what happened next**: one `--recent` search on
  the same subject (and `--since` the date you found), across all sources, not just the one
  that answered. Follow-ups change answers: a past-due invoice later escalates to an account
  suspension, a contract term gets renegotiated in WhatsApp, a Basecamp task gets a newer
  comment. Mention such findings even if not asked; they are usually what the user needs.
- Search excerpts can mislead (a reply quoting an old message, a forwarded thread): `get`
  the document before stating a fact, date or amount from it.

## Answering

Cite what you found: source, date, who said it, and the `url` when there is one (Gmail,
Drive and Basecamp links open the original). Quote short bits verbatim, especially Arabic,
rather than paraphrasing names or numbers.

## Coverage and limits

- Chats are one doc per message; WhatsApp history comes from an iPhone backup plus live
  WAHA, iMessage from the Mac (pushed hourly). Gmail skips Promotions/Social. Basecamp Pings
  have no API, so they are absent; deleted Basecamp items can linger.
- A query can fail with `vector_embedding_error … timeout` while a big re-embed is running
  on the GPU. Retry, or fall back to `--ratio 0` (keyword only, no embedding needed).
- `omni: command not found`: the CLI is installed from the repo with
  `uv tool install --editable ~/Projects/omni` and reads `~/Projects/omni/.env`
  (`MEILI_URL`, `MEILI_MASTER_KEY`). It only works on the home LAN / tailnet.
- Web UI, code, ingest and
  architecture: `~/Projects/omni/CLAUDE.md`.
