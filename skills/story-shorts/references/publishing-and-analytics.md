# Publishing, scheduling and analytics

Read `../SKILL.md` first. Reference kit: `<story-repo>/projects/youtube-stories/analytics.md`,
devlogs `claude_2026-10-14-youtube-first-uploads.md`, `claude_2026-10-15-youtube-swaps.md`,
`claude_2026-10-17-khaled-uploads.md` in `<story-repo>/docs/devlog/`, and each episode's `upload.yaml`.

## Before upload

- **Gate on the hash**: the file's sha256 must equal the one the critic cleared (record it in the episode's upload
  record). Any edit after the critic → delta critic → new hash.
- Metadata per episode: title (≤ 60 chars, statement), description (sources, credits for CC-BY assets and footage,
  AI line, "events as of <date>" for news), hashtags, category, language, "not made for kids", altered/synthetic
  content = Yes when the rules require it, no paid promotion. Never pair government footage with a sponsor.
- Re-check news-dependent stories on the day they go live.

## Upload and schedule (YouTube)

- **An unverified channel gets ~10 uploads per rolling 24 h**, not reset at midnight; plan a batch over two days and
  start each day after the previous day's upload times. Phone verification lifts it and makes description links
  clickable.
- **Swaps:** YouTube cannot replace a video's file. Upload the new cut, schedule and verify it, then set the old one
  **Private** (never delete); record `replaces:` and keep both ids in the history. Fix everything before the first
  upload.
- **Verify in the UI after a reload**, never from the click: read the confirmation dialog, reload the Shorts content
  list, hover each row to read its scheduled time and time zone, count rows, check for stray drafts.
- **Browser automation traps:** extension upload helpers may cap files (10 MB) — chunk and reassemble, then check the
  sha256 of the in-page file; release big `File`s (the tab crashed holding ~6 × 30 MB); if the extension can't drive
  the native picker, drive the real browser (`xdotool`, type the absolute path, click Open); read the clipboard back
  before pasting non-Latin titles; screenshot before every click (layouts shift); identify browsers/accounts by what
  they show, not by index; switch a shared browser profile back to the default channel afterwards.
- **TikTok:** photo carousels can't be posted from the web uploader; post them from the phone. Wait out TikTok's
  content check before clicking Post (the click silently does nothing while it runs), and verify the post exists in
  the account's item list.
- **Cadence:** a few a day at fixed slots beats bursts; each slot its own different-looking episode.

## Analytics loop (24–72 h after going live)

- Record per video, dated, read-only: views, engaged views, stayed-to-watch vs swiped-away, average view duration and
  % viewed, the retention curve at 0/1/3/10/30 s and the end, traffic sources, subscribers gained.
- The retention curve takes up to ~2 days to process; until then "stayed vs swiped" is the best opening signal.
- **Read the curve against the script's word times**: the measured biggest drop (108 → 76% at 0:04–0:06) landed on the
  place/year line, which is how the second-hook rule was found.
- Feed findings back as rules in the channel's docs, with the evidence. Single-video comparisons over a day are
  anecdotes, not tests — say so.
