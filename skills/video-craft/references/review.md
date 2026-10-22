# Review: nobody ships what nobody looked at

Read `../SKILL.md` first. Specs, logs and "render OK" lie; only pixels and audio tell the truth. On one batch 6 of 15
generated images with clean specs were rejects, and a payoff callout silently never drew in two episodes that
passed `--check`. Sources: `<story-repo>/.claude/agents/ugc-critic.md` (the reference critic agent),
devlogs `claude_2026-10-14-cutaway-12-16-rewords-and-critic.md`, `claude_2026-10-15-perfect-loop.md`,
`claude_2026-10-17-ep08-ep09-hold-fix.md` in `<story-repo>/docs/devlog/`.

## The loop

1. **Self-check while building**: 3 stills per shot (0.1 / 0.5 / 0.9 of it) before the full render; fix framing there,
   it is 10× cheaper than after.
2. **Render the final file**, then hand it to an **independent critic** (a subagent that did not build it) with the
   claim sheet and the spec. It must open the pixels: a contact strip plus frame 0 on its own (frame 0 is the
   thumbnail and the hook). Anything it did not open is reported "not reviewed", never passed.
3. **Verdict:** SHIP / SHIP with nits / FIX FIRST / SCRAP, then blocking defects, a per-asset/per-beat table, and the
   three highest-leverage fixes, each specific ("at 12.4 s the label covers the subject"). Blunt, no invented problems.
4. **Apply every FIX FIRST, re-render, and run a delta critic** on what changed. Any edit after a critic pass —
   even one line of script — needs a new pass: two Shorts were held because a post-critic open-loop line failed.
5. **Gate shipping on the file hash** the critic cleared; a re-render changes it.
6. **Read past verdicts first.** Before reusing any asset, read every sidecar `status`/`feedback`; the prose holds the
   direction, the status is only the floor.

## What to look at

- **Contact strip:** frames at 0, 1, 2.5 s, then every ~3 s plus the last frame, tiled
  (`ffmpeg -vf "select=…,scale=270:-1,tile=…"` or `magick … +append/-append`). Add frames on both sides of every
  counter, callout and payoff word.
- **Loop pair:** frame 0, the last frame and a ×4 difference image side by side; outside the caption band the mean
  difference should be ~1–5/255. Reference script: `<story-repo>/projects/youtube-stories/tools/_test/loop_pair.py`.
- **Timing dump:** word times vs shot windows vs overlay times. Checkers that only warn on never-shown overlays miss
  *late* ones; an overlay shown < 0.4 s is a defect.
- **Frame count:** `ffprobe -count_frames` after any change to the final pass.
- **Black frames:** `ffmpeg -vf blackdetect` on anything 3D or GPU-rendered.

## Pixel defects only the image shows

Accidental bodies (dark cloth on furniture reads as a corpse; faces in folds; extra limbs and fingers; figures in
mirrors), floating objects, baked borders/vignettes/film edges, garbled or invented text on signs and documents, an
extra object (a fifth bomb in a four-bomb story), an inset panel inside a 9:16 still, phone camera UI baked in, a
mouth open mid-speech with no speech, the wrong person/persona, a product that changes between cuts, a label on a
part not yet drawn, text in the platform-UI zones, a label landing mid-camera-move.

## Audio checks

- **ASR every take** against the script: every word present, especially the **last** words and anything after an
  ellipsis. Use two transcribers when one is doubtful; a re-roll can lose words that used to be there.
- **Homographs (same letters, different vowels/shadda) are invisible to ASR.** Clip the word ± one word and ask an
  audio model for an open-ended romanization ×3 (never a leading "A or B?"), or listen.
- `ebur128` for integrated loudness and true peak; `silencedetect -35 dB` for dead air at the start, end and seam.
- **List timestamps for a 10-second human listen** (names, numbers, homographs, the punchline). Nobody listening by
  ear is the gap automated checks leave.
