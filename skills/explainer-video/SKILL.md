---
name: explainer-video
description: Make an explainer / documentation video for ANY technical or software system (Remotion + OpenAI TTS + word-timed subtitles) at 3Blue1Brown/Fern level - purposeful motion, whole-architecture graphs, a hard length cap. Use whenever asked for an explainer, walkthrough, architecture or migration video, a PR/diff video, or "video that explains X" about code or a system. For true-story / history / entertainment Shorts use story-shorts instead.
---

# Explainer videos (code, systems, PRs)

Guidelines for explaining **any technical or software system** on video: an architecture, a migration, a protocol, a
data pipeline, a failure model, or a pull request. The rules come from a demanding reviewer's feedback on a real
migration video (quoted in `system-explainer.md` under "Lessons, in the reviewer's words"). Use `remotion-best-practices`
as the router to the installed Remotion skills (creation, captions, layout, rendering) and read the ones that apply.

## Steps (follow in order)

1. **FIRST, before anything else: read `~/.claude/skills/video-craft/SKILL.md` and
   `~/.claude/skills/video-craft/references/remotion.md`.** They hold the shared craft and Remotion technique this
   skill relies on (start in the action, the video explains and the voice comments, word-timed captions, audio
   levels, render traps, the frame-review loop). Where they conflict with the **Identity** section below, Identity wins.
2. **Read the topic file:** `system-explainer.md` (next to this file) for every video, and also `pr-walkthrough.md`
   when the video is about a pull request or diff. Read
   `~/.claude/skills/video-craft/references/visual-clarity.md` while laying out scenes.
3. **Research first, in parallel.** One subagent per repo/area writes cited notes, "video-worthy facts" and "diagram
   ideas". Correct the brief from the code; it is often wrong.
4. **Narration:** JSON, one entry per scene, word-budgeted to the cap. Write symbols as spoken ("S V C, fleet, v1").
5. **Voice and captions:**
   1. OpenAI `gpt-4o-mini-tts` (voice `onyx`, calm-engineer instructions) per scene, through **Doomscroll** first. It
      is an OpenAI-compatible, credit-metered proxy, so no OpenAI key is needed. Use the OpenAI SDK with
      `base_url="https://doomscroll.build/api/agent/v1"` and the Doomscroll key as `api_key`. Load the key inside the
      script, never print it. Look first in `DOOMSCROLL_API_KEY`, else in
      `~/.config/doomscroll/credentials.json` → `["https://doomscroll.build"]["apiKey"]`, which the Doomscroll agent
      client's `doomscroll.mjs login` saves after a browser approval.
      - Fallback: with no Doomscroll sign-in, use the user's own `OPENAI_API_KEY` (environment or the project's
        `.env`) against OpenAI directly.
      - With neither, ask the user to sign in at doomscroll.build → Settings → Agent access, or to give an OpenAI key.
        Headless: fail with that error instead of asking.
      - A 402 from Doomscroll means out of credits. Fail, or fall back to `OPENAI_API_KEY` if it is set, but keep
        **one voice provider per video**: never mix providers across scenes.
   2. `whisper-1` word timestamps (`response_format=verbose_json`, `timestamp_granularities=["word"]`) through the same
      client, aligned back to the *script* words with difflib, so subtitles show the exact script.
   3. Reject clips shorter than ~250 ms per word (the API sometimes truncates audio).
   4. Speed up with pitch-kept ffmpeg `atempo` and scale the caption times to match.
   (Why and the traps: `~/.claude/skills/video-craft/references/remotion.md` § Voice and captions.)
6. **Motion beats per spoken cue, before coding.** A `useCue()("phrase")` hook returns the frame where a phrase is
   spoken and throws if it isn't in the narration. Re-point cues whenever the narration changes.
7. **Shared layout and motion primitives first:** one architecture layout module reused by every scene; primitives for
   a packet on a curved path (labelled, repeatable as a stream), ripple, countdown ring, camera pan/zoom, shake, round
   icon nodes, edges that draw in and retract, cylinders that fill. PR videos start from `pr-scenes.tsx`.
8. **Fan out one agent per 2–3 scenes.** Each owns only its files and verifies with `tsc` plus 5–10 rendered stills it
   actually looks at. Then integrate, contact-sheet every scene (`magick … +append/-append`), fix overlaps, render,
   and run the frame-review loop (`~/.claude/skills/video-craft/references/review.md`).
9. **Verify** with ffprobe: expected width/height, duration, and an audio stream. Check one still per scene with a
   caption on screen for clipped text and overlaps.
10. **Deliver:** burned-in subtitles plus a sidecar `.srt`; each scene its own composition so one can be re-rendered.
    PR videos: encode and placement in `pr-walkthrough.md`. Outside PRs, make a < 30 MiB copy (`-crf 27`) for chat
    uploads.

**Headless runs** (a worker spawned with a prompt, e.g. `/explainer-video …`): write final artifacts only to the
absolute paths the prompt gives, render locally, and never stop to ask a question; where a step says "ask", fail with
a clear error instead.

## Identity (wins over video-craft on conflict)

| | This skill's look and feel |
|---|---|
| Bar | **YouTube-explainer level (3Blue1Brown, Fern), never PowerPoint.** Every movement explains something. If the viewer has to read text or imagine a mechanism, the scene failed |
| Format | **Portrait 9:16, 1080 × 1920 by default** (phone feed). Landscape 1920 × 1080 only when asked. Reflow diagrams vertically for portrait; never shrink or crop a landscape layout into it |
| Captions | **Sit high, never hugging the bottom edge**: players draw controls and progress bars there. Landscape: the caption box's `bottom` is ≥ 68 px on a 1080-tall canvas. Portrait: the caption band sits at y1180–1300 |
| Feed overlays (portrait) | If the video plays in a feed with a bottom info panel and a right action rail, keep essential content inside x160–820, y220–1120 and captions in y1180–1300; reserve the bottom 600 px and right 180 px. Check frames in a 390 × 844 viewport with `object-fit: cover`. Reflow scenes rather than shrinking text (`pr-scenes.tsx` exports this box as `SAFE`) |
| Voice | OpenAI `gpt-4o-mini-tts`, `onyx`, calm engineer. One voice for the whole video |
| Narration | **The video explains, the voice only comments** (owner's rule, 2026-10-22). You have a bias toward explaining with words, on-screen text and voice; fight it. The diagrams, components and their motion carry the explanation; narration is short, present tense, names what is moving right now, **≤ 12 words per beat, ~70 words a minute of video**. If a sentence explains something the animation could show, cut the sentence and animate it |
| Screen | **Never a blank or text-only screen while the narrator talks.** No title card, text wall, bullet list or empty stage under narration, not even at the start: open mid-action (a request already flying). The real components stay on screen the whole video; when nothing new happens, they at least sit there with data still flowing between them. Keep the stretches where the visuals are idle as short as possible |
| Show, don't narrate | The best beat teaches what the narration never says: a crashed worker visibly replaced by a new one flying into its slot says "it self-heals" without a word |
| Length | **Hard length cap.** "5 min max" means ≤ 5:00 including gaps. Budget words first (≈ 170 words/min raw), then speed up 1.25–1.36× with pitch preserved. Adding a scene means cutting another. PR videos have their own length and tempo (1.2×) in `pr-walkthrough.md` |
| Diagrams | Whole-architecture graphs, shaped nodes with real logos, motion that encodes behaviour (`system-explainer.md`) |
| Chapters | PR videos always carry the chapter progress bar (`pr-walkthrough.md`) |

## Icons and shapes

Every node gets a shape that says what it is, and a real logo when it is a real product. Never a row of identical
rectangles.

- **Iconify has every open icon.** It serves about 275k icons from every open set through one API, so search there
  first: `curl 'https://api.iconify.design/search?query=redis&prefixes=logos,devicon,simple-icons'`, then fetch
  `https://api.iconify.design/<set>/<name>.svg`. `logos` has full-colour product marks (`logos:redis-icon`), and `lucide`
  or `tabler` have generic shapes (`lucide:database`). `icons/find.sh <word>` runs the search.
- **Offline copies.** `icons/fetch.sh` downloads Simple Icons, Lucide, Tabler and Devicon into `icons/` (git-ignored,
  about 150 MB) for work without network.
- **Use them inline.** Read the SVG and paste its paths into a component, so the render needs no network. Simple Icons
  are one `path` in a 24×24 box, filled with the brand hex. Draw a near-black brand (GitHub, Vercel, Next.js) white on a
  dark stage.
- **Pick the shape from the role.** These are the defaults:

  | Role | Shape |
  |---|---|
  | Databases, caches and storage | Cylinders. |
  | People and devices | Round pills or circles. |
  | Services, workers and AI | Hexagons. |
  | Queues and streams | Stacks. |
  | Clients and browsers | Windows with a title bar. |
  | Code, files and config | Folded pages. |
  | Third parties | Dashed outlines. |
  | Fleets | Dot clouds. |
  | Process boundaries | Rings. |

  The Doomscroll renderer's `shapeOf` and `SHAPES` in `renderer/remotion/Explainer.tsx` implement this table as SVG
  outlines, and its `src/logos.ts` shows how to pick a logo from Iconify.

## Files in this skill

Deliberately plain paths, not `@` includes; step 2 says when to read each.

| File | What |
|---|---|
| `system-explainer.md` | Graph rules, the scene menu, content rules for technical narration, the reviewer's lessons |
| `pr-walkthrough.md` | PR/diff videos: NOW → THE CHANGE → BLAST RADIUS, the decision line and spotlight, numbered steps, chapter bar, length, <10 MB delivery |
| `pr-scenes.tsx` | Copy into the Remotion project for PR videos (`SAFE`, `ActTitle`, `NodeDot`, `StepFlow`, `BlastRings`, `DecisionSpotlight`, `ChapterBar`, `Caption`) |
| `icons/find.sh`, `icons/fetch.sh` | Iconify search; offline icon sets |

Sibling skills: `~/.claude/skills/video-craft/` (shared craft + Remotion; read first), `~/.claude/skills/story-shorts/`
(faceless true-story / history Shorts pipeline), `remotion-best-practices` (router to the official Remotion skills).
