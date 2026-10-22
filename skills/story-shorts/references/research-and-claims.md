# Topics, research and the claim sheet

Read `../SKILL.md` first. Reference kit: `<story-repo>/projects/youtube-stories/research/`
(`sources-and-rules.md`, `polysoldier-backlog.md`, `critique-facts.md`, `formats.md`).

## Topics

- **Mine successful channels' video lists sorted by views** (`yt-dlp --flat-playlist`, or the channel page). Their
  *story choice* is the signal ("this case already did 2.6M"); their telling is not ours. Pick from the top half: in
  the 3D-history reference, views fell off below ~500k.
- **Backlog table, one row per topic:** status (DONE / IN PROGRESS / candidate / SKIP + why), view signal, the
  audience angle (the detail that makes it close to *your* audience), hook, twist, 2+ sources, visual fit (does the
  format show the turn?), editorial fit. Then add new topics the reference never did. Rank the top 10 by view signal
  × editorial fit × visual fit. Example: `<story-repo>/projects/youtube-stories/research/polysoldier-backlog.md`.
- **Other lead sources:** Wikipedia "unusual articles" and categories ranked by pageviews (high pageviews in English
  + a thin or missing article in the target language = an unserved gap), public-domain archives (FBI Vault, NARA,
  DVIDS, Chronicling America, Wikisource classics), Reddit for discovery only.
- **Mechanism stories need spatial sources** (floor plans, engineering reports, court exhibits, sections); without
  them a cutaway diagram is invented.
- **Don't stack similar episodes:** two stories from the same era or palette back to back confound what the audience
  is responding to and look templated.

## Editorial line

Every channel has one (what it covers, whose side it takes, what it never shows). It lives in the channel's own
rules, never in this skill. It may steer story choice, angle and emphasis; it never licenses an invented or
unsourced fact. Label opinionated cuts as commentary.

## Retell events, never someone else's telling

- Facts and events are free; a competitor's script, a Wikipedia article's prose, or a Reddit post is not. Never hand
  an LLM a transcript or article to translate or adapt; that is a derivative work and fails "reused content".
- Build the beat order from the sources, not from the competitor's sequence. Write fresh from the claim sheet only.

## Claim sheet (`sources.md`, before any TTS)

```markdown
| # | Claim (as it will be said) | Source 1 (primary?) | Source 2 | Status |
|---|---|---|---|---|
| C1 | 1,700+ people died in one night | Kling et al. 1987, Science (primary) | USGS fact sheet | OK |
| C2 | the cloud moved at ~20 m/s | USGS | — | ONE SOURCE → hedge or cut |
```

- **≥ 2 independent sources per claim, one primary where it exists.** Wire copies (the same agency story in two
  outlets) count as one. Fetch them the same day (`curl`; if a .gov blocks bots, use the Wayback `id_` URL).
- **Read the primary, not the summary.** Summaries were wrong (a "DNA from a sandwich" that was a rubbish bag),
  self-contradicting (9 vs 10 days), and "pre-checked" quotes were not in the fetched text.
- **Hedge and attribute what is disputed or one-sided** («according to the Pentagon», "is believed to") — on the
  on-screen pill and the title as well as the voice. Say when a plan was never carried out.
- **Watch scope creep in hooks and titles:** "whole villages" when the source backs 1,700 people; "the money" when it
  was part of it; superlatives the source doesn't make; a presupposed cause. Give figures their base.
- **Drop disputed dates** rather than pick one; re-check anything ongoing (news, open cases) on publish day and date
  the description ("events as of <date>").
- **Every open-loop promise and every twist is a claim too**: it needs its row.

## Legal and platform

- Defamation is the main risk: prefer dead, historical or foreign subjects or final convictions; "alleged" for the
  living; never name private victims or bystanders; never give a real victim an AI voice.
- AI disclosure: stylised/3D/illustrated visuals need no label; a photoreal AI depiction of a real person or event
  does. When unsure, disclose.
- "Inauthentic content" (YouTube, July 2025): near-identical AI videos at volume. Each episode must differ in hook,
  structure and visuals from the last five; a shared intro/outro is fine.
