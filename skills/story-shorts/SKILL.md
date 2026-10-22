---
name: story-shorts
description: End-to-end pipeline for faceless YouTube Shorts / TikTok / Reels that tell true stories - history, mystery, heists, crazy-but-true, "how it works" mechanism Shorts, PolySoldier/OddFrame-style low-poly or x-ray 3D explainers, Fern/Zack D-style documentary Shorts - and for running a faceless channel's content pipeline (topic backlog, claim sheet, script, voice, visuals, render, critic, bilingual cuts, upload schedule, analytics). Use whenever asked for a "true story video", "history/mystery Short", "faceless YouTube/TikTok channel content", "make an episode", "a Short like <reference link>", or to batch, re-voice, schedule or analyse such Shorts. Not for code/PR explainers (explainer-video).
---

# Story Shorts: faceless true-story channels

## Steps (follow in order)

1. **FIRST, before anything else: read `~/.claude/skills/video-craft/SKILL.md` and
   `~/.claude/skills/video-craft/references/remotion.md`.** They hold the shared craft (hook, pacing, loudness, loop
   endings, the critic loop, the pre-ship checklist) and Remotion technique. Where they conflict with the
   **Identity** section below or the channel's own identity, the identity wins.
2. **Read the channel's own rules** (its `CLAUDE.md`, editorial line, locked voice, look, schedule) and every past
   reviewer verdict on assets you might reuse. A channel's rules beat this skill's defaults.
3. **Pick the topic** from a ranked backlog (`references/research-and-claims.md` § Topics).
4. **Claim sheet before any script line**: ≥ 2 independent sources per claim, one primary where it exists
   (`references/research-and-claims.md`).
5. **Write the script from the claim sheet** with a template (`references/script-templates.md`); write the hook, the
   second hook, the open loop and its payoff, and the loop line first.
6. **Voice it**: one TTS call per beat at the locked voice and speed; ASR every take; scan homographs; pronunciation
   lexicon (`references/voice-and-pronunciation.md`).
7. **Shot list on the word times**: 2–4 visuals per beat, something new every ~1–1.5 s, routes ranked real footage →
   motion graphics → 3D → generated stills (`references/visual-routes.md`). Layout stills before the full render.
8. **Render** (one spec → one mp4 + `.srt` + review sidecar; reuse cached takes; GPU offload for 3D).
9. **Critic loop on pixels** until SHIP or SHIP with nits (`~/.claude/skills/video-craft/references/review.md`), then
   a delta critic after every later edit.
10. **Bilingual cut** from the same shot list if the channel has a sister-language channel
    (`references/voice-and-pronunciation.md` § Bilingual).
11. **Upload / schedule and verify** in the platform UI; record ids, file hash and history
    (`references/publishing-and-analytics.md`).
12. **Read analytics after 24–72 h** and feed the drop points back into the next script.

Act as the manager for a batch: research → 2–3 samples judged by the owner → lock the format → subagents
mass-produce, one episode each, each with its own critic pass. Pause when a format is new; don't mass-produce an
unjudged pilot.

## Identity (wins over video-craft on conflict; a channel's own rules win over this)

| | Default for a faceless story Short |
|---|---|
| Format | 9:16, 1080×1920, 30 fps; **35–75 s** (full arc in one Short, no "part 2"); long-form 8–15 min is a separate template |
| Structure | Outcome-first cold open → "You see" → concrete numbers → "But…" → twist → loop line (`references/script-templates.md`) |
| Pacing | Brainrot motion (fast moves that settle, whips at scene changes, ≥ 1 event/s), natural voice (1.1–1.4×) |
| Voice | One locked narrator per channel (ElevenLabs `eleven_v3` worked best), calm documentary friend, never hype; never a real victim's voice |
| Captions | Word-timed karaoke chunks of 2–5 words (Arabic) or bare 2–3-word lines with a stroke (English), band ≈ y 0.70–0.78 |
| Look | One look per channel (low-poly 3D dioramas, x-ray cutaway, mannequin stills, archival collage), varied palette/camera per episode; people consistent within a video (a mannequin stays a mannequin) |
| Ending | Perfect loop into frame 0; last line flows into the first |
| Titles | Short past-tense statement + a number or one odd object + ≤ 1 semantic emoji, ≤ 60 chars |

## References (deliberately plain paths, not `@` includes; read each when its step comes up)

| File | Covers |
|---|---|
| `references/research-and-claims.md` | Topic backlogs from successful channels, editorial line, the "retell events, not tellings" rule, claim sheet format, hedging, legal risk |
| `references/script-templates.md` | Template A (Short), the PolySoldier structure, the cutaway format, long-form Template B, word budgets, a worked spec + shot list |
| `references/voice-and-pronunciation.md` | Voice choice and settings, speed, tags, dropped words, homographs, the lexicon + by-ear sheet, cost/caching traps, bilingual cuts |
| `references/visual-routes.md` | Ranked visual routes (PD footage, Remotion motion graphics, Remotion 3D / poly kit, generated stills), labelling, licences, consistency |
| `references/publishing-and-analytics.md` | Upload caps, swaps, verification in Studio, metadata, scheduling, reading retention curves |

**Reference implementation** (one channel's working kit; read when you need code, never copy its editorial line).
`<story-repo>` is a private repo; find it with `ls -d ~/Projects/*/projects/youtube-stories`, and if it is absent
build from the rules in this skill and `video-craft`:
`<story-repo>/projects/youtube-stories/` — `CLAUDE.md` (rules 1–10), `tools/README.md` (`make_story.py`
spec schema), `tools/remotion/README.md` (compositions incl. `Explainer3D` and the `poly` kit),
`research/formats.md`, `analytics.md`, `research/reference/*/ANALYSIS.md`, and `stories/26-urta-bulak-nuke-fire/build_spec.py`
(bilingual shot-list builder).

Sibling skills: `~/.claude/skills/video-craft/` (shared craft; read first), `~/.claude/skills/explainer-video/`
(code/system/PR explainers), `gemini-web-api` (free image/Veo generation), `remotion-best-practices`.
