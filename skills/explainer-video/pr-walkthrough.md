# PR explainers: help the reviewer decide

**Only for videos about a pull request or diff.** Other explainers skip the three acts, the chapter bar's PR act
names, the decision line and the spotlight; numbered sequence steps still help any video that walks a flow.

Read `~/.claude/skills/video-craft/SKILL.md` and `SKILL.md` next to this file first (SKILL.md step 1). This file only
adds what is specific to a PR, and its identity wins over video-craft on conflict. `pr-scenes.tsx` next to this file has the primitives.

## PR identity

From the gittok/doomscroll headless worker path (2026-10-22), which spawns `/explainer-video …`; these names and
paths are a contract with it.

- **Story:** a reviewer-decision story, NOW → THE CHANGE → BLAST RADIUS → "The decision: merging means you accept
  <risk> to gain <benefit>".
- **Beats are animated events** (send / fail / fix / pass / impact / decision). The narration only comments; never a
  title card or text wall under the voice.
- **Length:** 25–40 s, 90 s hard cap, unless the spawn prompt gives another length.
- **Chapter bar** low on the frame, just above the captions (Before / The change / After / Blast radius).
- **Real component names from the diff**, a shape per role (cylinder DB, hexagon service…) plus real product logos
  (`SKILL.md` § Icons and shapes).
- **Calm voice, pitch-kept tempo 1.2×**: the PR default, set on purpose by the owner (gittok `TEMPO 1.2`). A tempo in the spawn prompt still wins; the main skill's 1.25–1.36× is for non-PR explainers only.
- **Facts from the patch only.** Never claim tests passed, never invent a risk.

A PR video exists so a reviewer can decide whether to merge. It is not a tour of how the system works; a video that
only explains the architecture has failed. Reviewer's words: "highlight the blast radius and highlight the change, cuz
sometimes the entire video is just 'an explanation of how things work'".

## The three acts

1. **Now** (~20% of runtime): current behaviour, only the components the PR touches and their direct neighbours.
2. **The change**, highlighted on the *same* diagram: changed nodes/edges glow with a CHANGED / NEW / REMOVED tag,
   untouched ones dim, before transforms into after in place.
3. **Blast radius**: rings spread from the changed node and light exactly what they reach (callers, stored data, users,
   config, deploy/migration): red AT RISK, amber TOUCHED, grey SAFE. If nothing is reachable, the rings stop at the
   change and the narration says so.

## Decision, spotlight, numbered steps

- **State the decision** in act 2 or 3, narrated and captioned: "The decision: merging means you accept <risk> to gain
  <benefit>", or "No real risk here: <why>". Risks come from the patch (changed contract, migration, auth check,
  removed fallback, code every user hits); never invent one.
- **Spotlight where the decision lies:** dim everything, a pulsing ring and DECISION tag on the exact component, file
  or function (the hole includes its label), held ≥ 2 s.
- **Number every sequence:** whenever narration walks a flow (frontend → auth → backend → database), each hop gets a
  step badge 1, 2, 3… that pops on its arrow in order as the packet rides it and stays for the scene.

## Chapter progress line (always, on PR videos)

Split the video into 3–6 chapters you choose from its story (e.g. Context → Before → The change → After → Blast
radius → Decision; merge neighbouring scenes that play the same role). Show `ChapterBar` from `pr-scenes.tsx` for the
whole video, just above the captions: one segment per chapter sized by its length and filling as it plays, the
current chapter's name in that chapter's own color (it pops when the chapter starts), and the time left. Every chapter
gets a distinct color, and the scene's kicker uses it too. (Before 2026-10-22 this bar was on every explainer; the
owner moved it here as PR-specific. A long system explainer may still use it.)

## Primitives: `pr-scenes.tsx`

`ActTitle`, `NodeDot` tones, `StepFlow`, `BlastRings` + `blastTone`, `DecisionSpotlight`, `Caption`, `ChapterBar`,
laid out inside the feed's overlay-safe box (`SAFE`). Copy it into the project and feed it the PR's real components;
never ship the example data.

## Delivery

- **Encode under 10 MB:** H.264 ~512 kbps + AAC 64 kbps:
  `-c:v libx264 -b:v 512k -maxrate 600k -bufsize 1000k -preset slow -c:a aac -b:a 64k`.
- **Put the player at the top of the PR description** (keep the existing body), not in a separate comment.
