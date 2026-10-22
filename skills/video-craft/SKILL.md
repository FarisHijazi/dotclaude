---
name: video-craft
description: Shared craft for making ANY short video good - explainer, documentary, story or entertainment, 9:16 Shorts/TikTok/Reels or 16:9. Hook in the first frame, second hook at 2-6 s, open loops that pay off, something new on screen every 1-1.5 s, motion that settles, word-timed captions, natural-speed voice, loudness targets, perfect-loop endings, 9:16 safe areas, anti-template, fact-check discipline, the critic-looks-at-pixels loop and a pre-ship checklist; plus Remotion technique (compositions, captions, audio, @remotion/three 3D, GPU rendering). Use whenever making, scripting, editing, rendering or reviewing a video, Short, Reel, TikTok, explainer, motion graphic or animated diagram, and before the explainer-video or story-shorts skills.
---

# Video craft: what makes any short video good

The shared core for every video skill. Topic skills add only what is specific to them:
`~/.claude/skills/explainer-video/SKILL.md` (code, systems, PRs) and `~/.claude/skills/story-shorts/SKILL.md`
(faceless true-story / history / mechanism Shorts, the channel pipeline). If a rule applies to both, it lives here.

**A topic skill's Identity section wins on conflict.** This file sets defaults (a Short's pacing, loudness, safe
areas); a topic skill's own format, length, pacing, look, voice, caption style and structure override them. The
core never overrides a topic skill's identity, it only fills in what that skill leaves unsaid.

Deeper material, read on demand (deliberately plain paths, not `@` includes, so they cost nothing until needed):

| File | Read it when |
|---|---|
| `references/remotion.md` | Building or rendering in Remotion: setup, compositions, motion/easing, word-timed captions, audio mix and loudness, `@remotion/three` 3D, GPU rendering, render traps |
| `references/visual-clarity.md` | Laying out any frame: one idea per frame, hierarchy, callouts with leader lines, text sizes, contrast, 9:16/16:9 safe areas, diagrams that build step by step |
| `references/review.md` | Before showing anything to anyone: the critic loop, contact strips, loop-pair check, audio checks, what only pixels reveal |

`<story-repo>` is the owner's private repo that holds the reference story-Shorts kit; locate it with
`ls -d ~/Projects/*/projects/youtube-stories` (it may not exist on other machines — the rules here stand without it).
Sources cited as `[devlog <date-slug>]` live in `<story-repo>/docs/devlog/claude_<date-slug>.md`;
`[gittok/doomscroll, 2026-10-22]` is the headless PR-video worker that spawns `/explainer-video`;
`[analytics]` is `<story-repo>/projects/youtube-stories/analytics.md` (real YouTube Studio retention);
`[ref <id>]` is `<story-repo>/projects/youtube-stories/research/reference/<id>/ANALYSIS.md`;
`[explainer reviewer]` is the quoted reviewer in `~/.claude/skills/explainer-video/system-explainer.md`.

## 1. The opening is the whole funnel

96–99% of Shorts views come from the feed, so frame 0 and the first line decide everything [analytics].

1. **Start in the action. Frame 0 shows the payoff over a concrete, dramatic image** (or, in an explainer, an
   event already happening). No title card, no question card, no "welcome", no
   logo sting. Why: real footage + stated charge at frame 0 kept 65% of viewers; an illustrated question card kept
   38% [analytics 2026-10-16]. The frame-0 still doubles as the thumbnail, so it must read as a poster.
2. **Hook line ≤ 12 words, ~2–3 s, outcome first.** Why: 5–7 s hooks were flagged by every critic pass
   [devlog 2026-10-13-youtube-stories-scripts-v2].
3. **2–6 s is a second hook**: an escalation or the first "how?". Never place, year or background there; put
   where/when in an on-screen stamp. Why: the biggest measured drop, 108% → 76% in 2 s, landed exactly on a
   "City, year" line [analytics 2026-10-16].
4. **Open a loop early and pay it off by the last line** ("…but not because of what you think. Here's how", or for a
   list "…and the last one is insane"). Never tease what the content doesn't deliver. Why: owner, 2026-10-16: *"add
   things that get people to watch till the end"*; an unpaid tease is a lie the critic must fail.
5. **Statement titles, not questions**: short, past tense, outcome + a number or one odd object, one semantic emoji
   at most. Why: all top-12 titles of the 3D-history reference channel follow it; the question-titled run held worst
   [ref 91ij0H4ammY, devlog 2026-10-16-khaled-revoice-16-21].

## 2. Every second earns the next

6. **Something new on screen every ~1–1.5 s** (a cut, a pop, a callout, a camera move), never > ~3 s with nothing new.
   Why: organic reference Shorts run 0.6–0.8 cuts/s; the owner's verdict on one-still beats was *"I need more
   visuals. Animations. Maybe even 3D. Not just a single picture"* [ref LSa9iFbtinE, ref 91ij0H4ammY, devlog
   2026-10-16-jazari-visual-rework]. Measured target: 1.1–1.3 events/s.
7. **One idea per beat; 2–4 visuals per beat.** Zooms and arrows on one picture are the floor, not the target.
8. **The video explains, the voice only comments.** If a sentence explains what an animation could show, cut the
   sentence and animate it. Never a blank or text-only screen under narration. Why: *"the viewer has to imagine
   stuff"* and *"PowerPoint level"* were the two harshest verdicts [explainer reviewer].
9. **Motion is fast and then settles**: ease-out (`1-(1-p)^(1+pace)`, pace 2), punch-in zooms, whip pans with motion
   blur between scenes, a ~2% spring overshoot on landings. No long eased drifts, no slow motion (slow-mo reads as
   AI). Why: owner, 2026-10-14: *"the zoom in/out/motion is a bit slow… target brainrot adhd genz viewers"*
   [devlog 2026-10-14-brainrot-pace]. Exception: UGC/phone-recorded looks want a static or hand-held camera, no
   cinematic moves.
10. **Every movement explains something.** A fade-in on cue is not motion; a replacement flying into a dead node's slot
    is. Show the claim instead of labelling it [explainer reviewer].
11. **Cuts land on words.** Time shots from the word timestamps, not equal splits. Why: equal splits put counters and
    highlights 1–3 s late [devlog 2026-10-16-khaled-revoice-pilot].

## 3. Voice, captions, sound

12. **Voice at natural speed: 1.1–1.4×, never above 1.5×.** Pitch-kept `atempo` only. Why: the owner pulled 13 scheduled
    Shorts because *"I'm not liking… the fact that it's sped up"* (2026-10-16); 1.2× ≈ 12 chars/s ≈ 67 s per 800-char
    script. A slower read means more cuts, not longer ones.
13. **One TTS call per beat; the beat's measured audio length is its cut length.** No drift, no hand timing. **One
    voice per video**: if the main provider fails, the fallback voices the whole video, never a mix
    [gittok/doomscroll, 2026-10-22].
14. **Check the last words were spoken.** TTS drops words after an ellipsis and at take edges (a punchline was never
    voiced while its caption showed). ASR every take; check homographs by ear [devlog 2026-10-14-cutaway-12-16].
15. **Captions track the voice word by word**, 2–5 words per chunk, current word highlighted, never a 1-word orphan,
    inside the caption band (`references/visual-clarity.md`). Never reuse one caption box across beats: split into
    word chunks timed from the TTS durations [gittok/doomscroll, 2026-10-22]. Proofread every burned-in line aloud: pixels can't be
    fixed after posting.
16. **Loudness: master −14 to −16 LUFS integrated, true peak ≤ −1 dBTP (we land −3 to −4).** Music bed **12–20 dB
    under the voice**, its own bed per video. Why: references measured −14.4 to −15.5 LUFS with beds 12–20 dB under
    [ref 84cZpyrf_g4, ref LSa9iFbtinE]; our first bed at volume 0.35 sat ~28 dB under and was inaudible; one drone
    under every video is the "inauthentic content" pattern. Recipes in `references/remotion.md` § Audio.

## 4. Endings, format, originality

17. **Shorts end on a perfect loop.** The last ≤ 0.6 s returns to frame 0's picture and overlays (or a whip hides the
    seam), the last line flows grammatically into the first, and there is no silence at the seam. Why: YouTube
    auto-replays Shorts; owner, 2026-10-14: *"make the end have almost the same frame as the start"*.
18. **Design for 9:16 first**: essential content in the central ~70% width, nothing in the bottom ~20% or the right
    rail. Reflow layouts, never shrink or crop a 16:9 one in (`references/visual-clarity.md`).
19. **Anti-template.** Each video differs from the last five in hook device, structure, palette, camera path and
    music. A shared intro/outro is fine. Why: near-identical AI Shorts at volume is the pattern YouTube's July 2025
    "inauthentic content" rule names.
20. **Length is a hard cap** set before writing. Budget words first; adding a scene means cutting one.

## 5. Truth

21. **Every factual claim has ≥ 2 independent sources (one primary where it exists) on a claim sheet before any TTS.**
    Wire copies count as one. Hedge and attribute anything disputed, on screen as well as in the voice. Read the
    primary, not the summary. Why: the Wikipedia summary was wrong or self-contradicting in several episodes, and
    invented claims earn misinformation strikes.
22. **A specific wrong number is worse than a vague true one.** Round numbers ("10k+", "~45 min"); never invent a
    fraction, price or superlative. Trimming for length makes hooks overstate: re-check the trimmed line.
23. **Animate only what is true.** Verify a mechanism exists before animating it; label illustrations as
    illustrations; label real footage with its source and date; disclose photoreal AI of real people or events.

## 6. Nobody ships what nobody looked at

24. **A critic that looks at pixels reviews every render before anyone else sees it**, and again after every fix
    (a delta critic). Specs lie; 6 of 15 "clean" generated images were rejects. Verdicts: SHIP / SHIP with nits /
    FIX FIRST / SCRAP. Procedure in `references/review.md`.
25. **Read every past verdict and feedback before reusing an asset.** Reused rejected clips once forced five finished
    videos to be rebuilt.
26. **Never delete intermediates**; archive superseded cuts to `_superseded/<stamp>-<why>/`. Re-edits are routine.

## Pre-ship checklist

- [ ] Frame 0 is a poster: the payoff over a concrete image, readable at thumbnail size.
- [ ] Hook ≤ 12 words; 2–6 s is a second hook, not place/year.
- [ ] Every open loop is paid off by the end, and the payoff is true to the claim sheet.
- [ ] Nothing on screen holds > ~3 s without something new; ≥ 1 event/s overall.
- [ ] Every beat's visuals show what the voice says, on the word.
- [ ] Voice at 1.1–1.4×; ASR shows every word spoken, especially the last; homographs checked by ear.
- [ ] Captions word-timed, in the band, proofread; no text in the bottom 20% or right rail.
- [ ] Master −14 to −16 LUFS, peak ≤ −1 dBTP, bed 12–20 dB under the voice, no dead air at start or end.
- [ ] Loop pair (frame 0 vs last frame) checked by eye; last line flows into the first.
- [ ] Claim sheet: ≥ 2 sources per claim; hedges on screen too; illustrations and footage labelled.
- [ ] Different hook, structure, palette and music from the last five.
- [ ] Critic verdict SHIP or SHIP with nits on the final file; its FIX FIRST items applied and re-checked.
- [ ] ffprobe: resolution, duration, an audio stream; file hash recorded where it will be uploaded.
