# Script templates and a worked example

Read `../SKILL.md` first; the hook/second-hook/loop rules are in `~/.claude/skills/video-craft/SKILL.md` §1 and §4.
Measured formats: `<story-repo>/projects/youtube-stories/research/formats.md` and
`research/reference/{91ij0H4ammY,LSa9iFbtinE,84cZpyrf_g4}/ANALYSIS.md`.

## Word budgets

- One beat = one TTS call = 1–3 short sentences = 2–4 visuals.
- At a natural 1.2× read: Arabic ≈ 12 chars/s → **~800 spoken chars ≈ 67 s**; English ≈ 2.7–3 words/s → **~150–170
  words ≈ 60 s**. Time a beat sheet on the real voice before locking; budgets taken from another voice ran 15–35% long.
- Don't speak full dates or places in the opening: they go in a stamp (a spoken year costs ~2.5 s and the 2–6 s drop).

## Template P — outcome first (the 3D-history reference structure, 57 s)

| # | Time | Beat | Rule |
|---|---|---|---|
| 0 | 0–8 s | **Outcome** | The absurd result in one or two sentences: who + what + the consequence |
| 1 | ~8 s | **"You see,"** | The turn into a chronological retelling |
| 2 | 8–45 s | **Numbers** | Concrete numbers carry it: ages, counts, prices, times ("100 smoke detectors at $1 each", "2:40 AM") |
| 3 | ~45 s | **"But…"** | Set up the twist ("But they were too late.") |
| 4 | 45–56 s | **Twist + quote** | The detail nobody expected, ideally a real quote; it pays off the open loop |
| 5 | last line | **Loop line** | Flows grammatically into the first line |

The open loop is implicit (*how does that happen?*); add an explicit one in the 2–6 s window when the outcome alone
doesn't promise a twist ("…but not for the reason you think").

## Template A — mystery / crime Short (60–75 s)

0 HOOK (payoff or an unexplained image, ≤ 12 words) → 1 SECOND HOOK (escalation or first "how?", place/year in a
stamp) → 2 FIRST CRACK ("But…") → 3 ESCALATION ×2 (re-hook every ~10 s: "then another", "what nobody knew…") →
4 REVEAL (name it plainly, hold the visual) → 5 AFTERMATH or OPEN LOOP (solved: the outcome in one line; unsolved:
the last unanswered question) + loop line. No spoken "subscribe".

## Format C — cutaway tour (30–50 s)

One label-free isometric cutaway of where it happened; a persistent statement title; the camera tours region by
region and a callout with an arrow pops on the word that names each part; flow arrows for the mechanism. Needs
spatial sources. Measured reference: no cuts at all, but a dense labelled diagram — copy it only with a real story
and visible editing, or it is a slideshow.

## Template B — long-form (8–15 min)

Silent or one-line cold open (the strangest image, unexplained) → the promise → Act 1 the world (named person,
present tense, first crack) → Act 2 investigation (evidence as documents/maps in the scene, re-hook every 60–90 s,
mid-roll after a re-hook) → Act 3 the twist (the one zenith) → Act 4 climax → aftermath → the last loop.
Every chapter ends on a question the next half-answers.

## Worked example (condensed from a real episode)

Story: the Soviet Union put out a three-year gas-well fire with a nuclear charge (Urta-Bulak, 1966). Template P,
~61 s English / ~64 s Arabic, one voice per language, every shot a low-poly 3D diorama. Every number below is a row of
that episode's claim sheet (`<story-repo>/projects/youtube-stories/stories/26-urta-bulak-nuke-fire/sources.md`,
U1–U20); do not reuse them without your own sources.

| Beat | VO (English cut, abridged) | Visuals (each on its word) |
|---|---|---|
| 0 Outcome | "The Soviet Union put out a gas fire… with a nuclear bomb." | Night derrick in flames as the frame-0 poster; amber callout on the flame |
| 1 Second hook + open loop | "Twice the size of Hiroshima, and the flames died in 23 seconds. But when they tried it in Ukraine? Nobody saw that coming." | Whip → "23 s" card; tilted map card of Ukraine with a "?" |
| 2 "You see" | "You see, in 1963, a gas well in Uzbekistan blew out… and caught fire." | Stamp "1963 · UZBEKISTAN" (place/year on screen, not the hook) |
| 3 Numbers | "Every day it burned over 12 million cubic meters of gas." | Counter landing just before "12"; gas plume |
| 4 Failed attempts | "They tried water, sand, foam… even artillery. It burned for almost 3 years." | One quick shot per attempt, red "FAILED" + dashed ring each |
| 5 Mechanism | "They drilled a slanted well, nearly a mile deep… then lowered in a bomb worth 30,000 tons of TNT." | Ground cutaway: strata, the slanted bore drawing in on "slanted", the charge at the bottom |
| 6 Payoff | "The blast sealed the well from below. 23 seconds later… the fire was out." | Underground blast ring → flame snaps off on "out" |
| 7 Twist (pays the loop) | "Six years later in Ukraine, they nuked another burning well. But the fire didn't go out." | Same set at dusk; a bigger column and mushroom cloud; red alarm label |
| 8 Loop line | "…till crews put it out the old way. No nukes." → flows back into beat 0 | Return to the frame-0 framing; a whip hides the seam |

**Spec skeleton** (abridged from that episode's `spec-en.yaml`; the renderer's schema is in the reference kit's
`tools/README.md`, and the real spec is GENERATED by `build_spec.py`):

```yaml
name: nuke-fire-en
aspect: "9:16"
tts: elevenlabs            # the channel's locked voice and speed; one voice for the whole video
voice_id: <locked voice id>
voice_name: <locked narrator>
model: eleven_v3
speed: 1.15
caption_style: {animated: false, pill: false, stroke: 7, y: 0.74, size: 74, max_words: 3}
music: {path: music/bed.mp3, volume: 0.5, duck: false}  # measure: bed 12-20 dB under the VO
beats:
  - narration: "The Soviet Union put out a gas fire... with a nuclear bomb."
    shots:
      - remotion: {comp: Explainer3D, props: {...}, dur: auto}   # props: tools/remotion/README.md § poly
  - narration: "You see, in 1963, a gas well in Uzbekistan blew out... and caught fire."
    shots:
      - remotion: {comp: Explainer3D, props: {...}}
        overlays: [{type: stamp, text: "1963 · UZBEKISTAN", type_ms: 0}]
  # … one entry per beat; shot times written in seconds on the word times, converted to shot fractions by a builder
```

**Bilingual from one shot list:** keep every on-screen string as a `(lang1, lang2)` pair in one builder script that
writes both specs; shot *fractions* are shared, only lengths change with each voice's beat length. Re-check pops in
the shorter language's shots (a label can land late and hold 0.5 s).
