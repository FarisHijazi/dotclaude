# Visual clarity: frames a viewer understands at a glance

Read `../SKILL.md` first. A topic skill's Identity section (its own caption band, safe box, palette) wins over the
defaults here. Sources: `<story-repo>/docs/devlog/claude_2026-10-13-somerton-v2-render.md`,
`claude_2026-10-14-ep13-boston-molasses-cutaway.md`, `claude_2026-10-14-ep14-chernobyl-cutaway.md`,
`claude_2026-10-21-3d-explainer-pilot.md`, `claude_2026-10-22-polysoldier-format.md`, and the explainer reviewer in
`~/.claude/skills/explainer-video/system-explainer.md`.

## One idea per frame

- **One subject, one claim per beat.** If the frame needs a legend, it holds two ideas; split the beat.
- **Build diagrams up step by step on the word that names each part**, never all at once. The full diagram appears
  only once the viewer has met every piece. A mechanism plays as cause → effect in order, each step on its word.
- **Keep the map.** Reuse one layout across scenes (the same architecture graph, the same 3D set, the same map
  framing) so the viewer always knows where they are; the camera moves within it rather than cutting to new layouts.
- **Show the whole range on the real objects**: when a rule has variants, light up exactly what each one matches.
- **Close-ups of a diagram must still show its identifying parts**; end the previous beat wide when the next opens
  tight, or a callout lands on something unrecognisable.

## Hierarchy

- **Three levels at most:** the subject (largest, highest contrast), the callout naming it, then context dimmed to
  ~30–40%. Dim everything that isn't being talked about.
- **Colour means something**: one accent for "this", one alarm colour (red) for danger/failure, grey for context.
  Never decorative rainbows.
- **Shapes say roles** (cylinders for storage, hexagons for services, people as pills/mannequins…); identical boxes
  in a row read as PowerPoint. The explainer skill keeps the shapes-by-role table and Iconify how-to
  (`~/.claude/skills/explainer-video/SKILL.md` § Icons and shapes); products get their real logo.

## Callouts and labels

- **A label points at its object with a leader line ending in an arrow or dot**; the leader draws first, the text
  pops after (~6% overshoot). Place the label in clear space, never over the subject.
- **Pin labels to the object**, not the screen, when the camera moves (project 3D/image coordinates to pixels each
  frame), and keep them inside the safe box at every keyframe of the move.
- **Alarm callouts:** red text plus a dashed ring around the thing that matters (`[ref 91ij0H4ammY]`).
- **Time and place go in a stamp**, not the voice: a short tilted card or a top stamp ("10 MONTHS LATER").
- **Labels come from the renderer, never from an image model** (generated text garbles); label illustrations as
  illustrations ("illustrative"), and real footage with source and date.

## Text sizes and contrast (1080×1920)

| Element | Size | Notes |
|---|---|---|
| Hook / title | 84–110 px | 2 balanced lines max, ≤ 12 words |
| Captions | 64–74 px | 2–5 words, one line; shrink a too-wide chunk, never wrap |
| Callouts / stamps | 36–46 px minimum | Source lines smaller than ~30 px are unreadable on a phone |
| Big numbers | 100–112 px | 150 px counters ran off the frame |

- **Contrast:** white text with a ~7 px dark stroke or a 0.9+ opaque pill; the pill must contrast with the background
  and the text with the pill. Panels over footage at ~0.97 opacity.
- **Proofread every on-screen line aloud** before it is burned in; check every glyph exists in the font (tofu boxes).
- **Pill height** for Arabic fonts with tall line metrics (Kufi ≈ 2.2 em): ~1.45 × the font size.

## Safe areas

**9:16 Shorts / TikTok / Reels (1080×1920)** — the platform draws its UI over the video:

- Bottom ~20–30% (title, channel, music line, progress bar) and the right ~180 px (like/comment/share rail) are
  covered. RTL text starts on the right, under the rail, so centre it slightly left (x ≈ 0.46).
- **Essential content:** central ~70% of the width, y ≈ 0.11–0.70. **Captions:** a band around y ≈ 0.62–0.78 (topic
  skills pin the exact band). **Stamps/headlines:** top band y ≈ 0.11–0.27, below the status bar.
- Generated stills come at 3:4 and get cropped to 9:16: compose inside the central ~70% or the edges are lost.
- Check frames in a 390 × 844 viewport with `object-fit: cover`, with a mock of the UI overlay if you have one.

**16:9 (1920×1080):** captions with `bottom` ≥ 68 px (players draw controls there), titles inside a ~5% margin.

**Never shrink or crop a 16:9 layout into 9:16**: reflow it vertically. Put 16:9 footage on a blurred, darkened copy of
itself (letterbox) at scale 1.0–1.6 instead of a centre crop (a crop kept 32% of the width and lost the subject).

## Motion for clarity

- **Every movement explains something**: packets ride from the exact producer to the exact consumer; a failure is a
  node dying and the replacement flying in; a range is the matching dots lighting.
- **Camera moves to the next thing being said**, then settles before the label lands; a label landing mid-move is
  unreadable.
- **Behaviour distinguishes similar things**: two storage types *behave* differently on screen rather than carrying
  different text.
