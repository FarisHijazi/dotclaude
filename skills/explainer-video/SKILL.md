---
name: explainer-video
description: Make an explainer / documentation video for ANY technical or software system (Remotion + OpenAI TTS + subtitles) at 3Blue1Brown/Fern level - purposeful motion, whole-architecture graphs, a hard length cap. Use whenever asked for an explainer, walkthrough, architecture or migration video, or "video that explains X".
---

# Explainer videos

Guidelines for explaining **any technical or software system** on video: an architecture, a migration, a protocol, a
data pipeline, a failure model. The rules come from a demanding reviewer's feedback on a real migration video (quoted
under "Lessons, in the reviewer's words"). Use `remotion-best-practices` as the router to the installed Remotion skills
(creation, captions, layout, rendering) and read the ones that apply.

## Setup: install the Remotion skills first

If `remotion-best-practices` isn't among the available skills, install Remotion's official skills
(<https://github.com/remotion-dev/skills>) with the `skills` CLI, then read the ones that apply:

```bash
npx -y skills add remotion-dev/skills --global --skill '*' --agent claude-code --yes
```

Drop `--global` to install into the current project instead. `npx -y skills add remotion-dev/skills --list` shows
what the repo ships (best-practices, create, captions, markup, render, studio, ...).

## Output format

- **Portrait 9:16, 1080 × 1920 by default** (phone feed). Landscape 1920 × 1080 only when asked. Reflow diagrams
  vertically for portrait; never shrink or crop a landscape layout into it.
- **Subtitles sit high, never hugging the bottom edge**: players draw controls and progress bars there. Landscape: the
  caption box's `bottom` is ≥ 68 px on a 1080-tall canvas. Portrait: the caption band sits at y1180–1300.
- **Feed overlays (portrait):** if the video plays in a feed with a bottom info panel and a right action rail, keep
  essential content inside x160–820, y220–1120 and captions in y1180–1300; reserve the bottom 600 px and right 180 px.
  Check frames in a 390 × 844 viewport with `object-fit: cover`. Reflow scenes rather than shrinking text.
- **Chapter progress line (always):** split the video into 3–6 chapters you choose from its story (e.g. Context →
  Before → The change → After → Blast radius → Decision; merge neighbouring scenes that play the same role). Show
  `ChapterBar` from `pr-scenes.tsx` for the whole video, just above the captions: one segment per chapter sized by its
  length and filling as it plays, the current chapter's name in that chapter's own color (it pops when the chapter
  starts), and the time left. Every chapter gets a distinct color, and the scene's kicker uses it too.
- **Verify** with ffprobe: expected width/height, duration, and an audio stream. Check one still per scene with a
  caption on screen for clipped text and overlaps.
- **PR explainers:** H.264 ~512 kbps + AAC 64 kbps, under 10 MB:
  `-c:v libx264 -b:v 512k -maxrate 600k -bufsize 1000k -preset slow -c:a aac -b:a 64k`. Put the player at the top of
  the PR description (keep the existing body), not in a separate comment.

## The bar

**YouTube-explainer level (3Blue1Brown, Fern), never PowerPoint.** Every movement explains something. If the viewer has
to read text or imagine a mechanism, the scene failed.

- **The video explains, the voice only comments (owner's rule, 2026-10-22).** You have a bias toward explaining with
  words, on-screen text and voice; fight it. The diagrams, components and their motion carry the explanation; narration
  is short, present tense, and names what is moving right now (≤ 12 words per beat, ~70 words a minute of video). If a
  sentence explains something the animation could show, cut the sentence and animate it.
- **Never a blank or text-only screen while the narrator talks.** No title card, text wall, bullet list or empty stage
  under narration, not even at the start: open mid-action (a request already flying). The real components stay on
  screen the whole video; when nothing new happens, they at least sit there with data still flowing between them.
  Keep the stretches where the visuals are idle as short as possible.
- **Show, don't narrate.** The best beat teaches what the narration never says: a crashed worker visibly replaced by a
  new one flying into its slot says "it self-heals" without a word.
- **Graphs, not lines.** Never a left-to-right chain of boxes. Draw the **whole architecture** as a graph (hub,
  fan-out, trees, rings) and reuse that layout in every scene so the viewer builds a mental map.
- **Migrations transform in place.** Show the full before-architecture; removed parts collapse (edges retract), the new
  part drops in, new edges grow. The most important scene of any migration video.
- **Point at the exact producer and consumer.** Every message, topic or API call is a packet travelling from the exact
  service that produces it to the exact ones that consume it. Coloured text alone isn't enough.
- **Show a concept's whole range on the real objects.** If a concept has variants (a wildcard matching one item, one
  group, everything), animate each and light up exactly what it affects on the actual diagram, 1:1.
- **Every table becomes an animation.** Each row of a failure / comparison / alternatives table is an animated
  before/after mini-story; end with a camera pull-back to a grid of all panels.
- **Abstract rules get a wordless story** (a bad actor tries, the rule stops it, nothing downstream notices).
- **Fewer squares.** Round icon nodes with glow, curved links, cylinders for storage, dot clouds for fleets, rings for
  process boundaries. Boxes only for code/data snippets.
- **Explain differences by behaviour.** Similar things (e.g. storage streams) each *behave* differently on screen: one
  fills and drops its oldest, one keeps only the latest per key, one flashes and vanishes unstored.
- **Truthful animation only.** Verify a mechanism exists before animating it, even when the requester suggests it, and
  say so when their example doesn't match the system. Mark plans as plans.

## Scenes to pick from

Each is a graph with motion, not a slide.

1. **Purpose and scale (~20 s):** what the system does, as data flowing through it; size as a dot cloud or counters.
2. **Whole architecture (the anchor):** every component in the one layout later scenes reuse.
3. **A request's journey:** one real call end to end, packets riding labelled arrows (sequence diagram or the graph).
4. **A data's journey:** produced, buffered, stored, consumed; storage as cylinders that fill.
5. **Addressing / routing:** how things find each other; light up exactly what each rule matches.
6. **Safety rules / invariants:** each as a short wordless story.
7. **Failure scenarios:** one animated before/after per failure, then a recap grid.
8. **Scale and availability:** replicas forming, a node dying, a leader moving, clients reconnecting while traffic flows.
9. **Before → after:** the old architecture transforms in place into the new one.
10. **Alternatives:** why not X, shown as jobs X can't absorb.
11. **What's next:** roadmap steps that visibly remove the remaining weak spots.

## PR explainers: help the reviewer decide

**Only for videos about a pull request or diff.** Other explainers skip the three acts, the decision line and the
spotlight; numbered sequence steps still help any video that walks a flow.

A PR video exists so a reviewer can decide whether to merge. It is not a tour of how the system works; a video that
only explains the architecture has failed. Reviewer's words: "highlight the blast radius and highlight the change, cuz
sometimes the entire video is just 'an explanation of how things work'".

1. **Now** (~20% of runtime): current behaviour, only the components the PR touches and their direct neighbours.
2. **The change**, highlighted on the *same* diagram: changed nodes/edges glow with a CHANGED / NEW / REMOVED tag,
   untouched ones dim, before transforms into after in place.
3. **Blast radius**: rings spread from the changed node and light exactly what they reach (callers, stored data, users,
   config, deploy/migration): red AT RISK, amber TOUCHED, grey SAFE. If nothing is reachable, the rings stop at the
   change and the narration says so.

- **State the decision** in act 2 or 3, narrated and captioned: "The decision: merging means you accept <risk> to gain
  <benefit>", or "No real risk here: <why>". Risks come from the patch (changed contract, migration, auth check,
  removed fallback, code every user hits); never invent one.
- **Spotlight where the decision lies:** dim everything, a pulsing ring and DECISION tag on the exact component, file
  or function (the hole includes its label), held ≥ 2 s.
- **Number every sequence:** whenever narration walks a flow (frontend → auth → backend → database), each hop gets a
  step badge 1, 2, 3… that pops on its arrow in order as the packet rides it and stays for the scene.
- `pr-scenes.tsx` next to this file has the primitives (`ActTitle`, `NodeDot` tones, `StepFlow`, `BlastRings` +
  `blastTone`, `DecisionSpotlight`, `Caption`) laid out inside the feed's overlay-safe box. Copy it into the project
  and feed it the PR's real components.

## Content rules

- **Hard length cap.** "5 min max" means ≤ 5:00 including gaps. Budget words first (≈ 170 words/min raw), then speed up
  1.25–1.36× with pitch preserved. Adding a scene means cutting another.
- **Round numbers:** "10k+", "~45 min", "~15 MW". Never "13,210×"; never stack numbers in one line.
- **Cut what doesn't explain:** side stories, deploy mechanics, rollback tooling, same-day incidents.
- **Say current vs planned and good vs bad** in the narration.
- **Exec summary (≤ 1 min):** what it was → what it became → what it unlocks. No internals.

## Lessons, in the reviewer's words

From a ~5-minute migration explainer (services moving from one central coordinator node to a clustered message bus)
plus a 1-minute exec cut. Each quote names the lesson it taught.

- **Depth on the core mechanics, not a rush past them:** "you didn't focus a lot on the streams and rps calls and the
  topics/subjects and all the benefits [...] and also that having another node/cluster allows us to have HA".
- **Length is a hard cap:** "the entire thing is fucking 8min wtf bro, I said 5min max" (v2 grew by adding scenes
  without cutting).
- **Rounded numbers, no side stories:** "13k or 10k is close enough, and the '..homemade probe...' sentence just isn't
  needed".
- **Whole architecture, animated change:** "this should have the entire architecture there and then you animate removing
  stuff and replacing them [...] why the fuck are all the diagrams linear!!!!! use graphs!!!"
- **Tie text to the diagram:** "it's just text and the viewer has to imagine stuff!!!!! actually draw arrows linking
  between those and the exact point in the architecture where the data is being produced and consumed".
- **Animate claims, don't label them:** "why the fuck don't you just animate a new supervisor taking its place?!!!"
  (the scene showed a "replaced in ~1 s" label instead).
- **Purposeful motion:** "the animations are weak as fuck, they're almost powerpoint animation level [...] each movement
  is meant to explain something" (scenes mostly faded boxes in on cue).
- **Motion that encodes unsaid facts:** "if there would've been a bunch of circles on standby that go ahead and replace
  the failed supervisor, that shows that there are hot standbys [...] be smart like that". The principle was right, but
  that system had no standby pool, so the video showed a fresh process spawning instead.
- **Every table animated:** "'what happens when..' should have an animation for every single scenario [...] along with
  all the other tables".
- **Abstract rule as a story:** epoch fencing "could be a billion times clearer visually". The fix, without words:
  controller 7 writes through a gate; it freezes, 8 starts and the gate rolls 7 → 8; 8's writes pass; zombie 7 wakes
  and every write shatters on the gate while the devices don't react.

What landed (do more of this):

- **Failover shown, not told:** "the servers redirect to the new failover [...] servers, that's what we need more of!"
  Three servers in a triangle; one dies, links snap, a leader star moves, each client swings to a survivor while
  traffic keeps flowing.
- **A concept's range on real objects:** a site map of dots; as the filter widens (one tank → one container → whole
  site) exactly the matching dots light up.
- **One call end to end:** four lifelines; each RPC step is a labelled packet riding its arrow as it's spoken (request
  with ID and deadline → routed → checks → stored → "accepted" → caller watches until done).
- **One concrete flaw, cause and effect together:** a pipeline with a hard buffer limit, and the bug step by step
  (insert fails → error logged → batch deleted anyway → DATA LOST stamp).

## Process

1. **Research first, in parallel.** One subagent per repo/area writes cited notes, "video-worthy facts" and "diagram
   ideas". Correct the brief from the code; it is often wrong.
2. **Narration:** JSON, one entry per scene, word-budgeted to the cap. Write symbols as spoken ("S V C, fleet, v1").
3. **Voice and captions:**
   1. OpenAI `gpt-4o-mini-tts` (voice `onyx`, calm-engineer instructions) per scene. Read `OPENAI_API_KEY` from the
      environment or the project's `.env`; ask where it lives if neither has it.
   2. `whisper-1` word timestamps, aligned back to the *script* words with difflib, so subtitles show the exact script.
   3. Reject clips shorter than ~250 ms per word (the API sometimes truncates audio).
   4. Speed up with pitch-kept ffmpeg `atempo` and scale the caption times to match.
4. **Motion beats per spoken cue, before coding.** A `useCue()("phrase")` hook returns the frame where a phrase is
   spoken and throws if it isn't in the narration. Re-point cues whenever the narration changes.
5. **Shared layout and motion primitives first:** one architecture layout module reused by every scene; primitives for
   a packet on a curved path (labelled, repeatable as a stream), ripple, countdown ring, camera pan/zoom, shake, round
   icon nodes, edges that draw in and retract, cylinders that fill.
6. **Fan out one agent per 2–3 scenes.** Each owns only its files and verifies with `tsc` plus 5–10 rendered stills it
   actually looks at. Then integrate, contact-sheet every scene (`magick … +append/-append`), fix overlaps, render.
7. **Deliver:** burned-in subtitles plus a sidecar `.srt`; each scene its own composition so one can be re-rendered.
   Outside PRs, make a < 30 MiB copy (`-crf 27`) for chat uploads.

## Traps

- Chrome dying during `remotion still/render`: look for unreadable directories on PATH and strip them.
- No system `ffmpeg`/`ffprobe`: use `node_modules/.bin/remotion ffmpeg|ffprobe` (lacks some filters, e.g.
  `volumedetect`).
- `npx`/`npm` must be the real Node binaries, not a bun shim.
- JSX text can't contain a bare `<` (`< 1 min`); wrap it in `{"…"}`.
- `while pgrep -f '<pattern>'` matches its own shell's command line and never exits.
- Stills taken mid-fade look washed out; that's the transparent PNG, not the video.
