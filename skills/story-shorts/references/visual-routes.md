# Visual routes, ranked

Read `../SKILL.md` first; Remotion and 3D technique (GPU rendering, GpuSync, glTF, hq mode) is in
`~/.claude/skills/video-craft/references/remotion.md`, frame layout in `~/.claude/skills/video-craft/references/visual-clarity.md`.
Reference kit: `<story-repo>/projects/youtube-stories/research/real-footage.md`,
`research/production.md`, `tools/IMAGE-ROUTE.md`, `tools/remotion/README.md`, `assets/3d/INDEX.md`.

**Budget: 2–4 visuals per beat, something new every ~1–1.5 s.** One still per beat is the floor, never the target.

## 1. Real public-domain footage and photos (first)

- Sources: DVIDS, NASA, NOAA, the US National Archives, Wikimedia Commons PD files, Prelinger; stock (Pexels,
  Pixabay) as filler only. Real footage held retention best (an opening on real footage with the charge stated kept
  65% of viewers vs 38% for an illustration).
- **Read every file's licence tag** (a "Navy" clip on Commons was CC BY, not PD) and keep a licence sidecar.
- Keep footage ≲ 40% of screen time, as evidence; your analysis (graphics, structure) is the original contribution
  and PD clips are on hundreds of channels.
- Cuts 1.5–3.5 s, never > ~4 s; several in-points across one source; skip its first/last ~2 s (slates, black).
- 16:9 into 9:16 on a blurred letterbox at scale 1.0–1.6, never a centre crop. Keep 16:9 masters; a pre-baked letterbox
  can't be enlarged later.
- **Label each cut on screen with source and real year.** Never: news-network clips, state media, other creators'
  footage, game footage passed off as real, or a photoreal AI "event" next to real footage.

## 2. Remotion motion graphics (free, the original contribution)

Animated maps (fly-in camera, fill wipes, drawn routes, pins), timelines, counters, bar charts, and **purpose-built
mechanism diagrams** (a moving cross-section of the machine, built step by step on the words). Use them instead of
still maps. Reference compositions: `AnimatedMap`, `Timeline`, `Counter`, `BarChart`, `CameraObscura`, `ElephantClock`
in the reference kit's `tools/remotion/src/`.

## 3. Remotion + Three.js 3D

- **X-ray mechanism explainer** (OddFrame style): a real model in a dark studio, ghost hull with bright edges, solid
  internals, mechanism events in order with slow motion on the key one, pinned thin labels, name plate, HUD. The
  owner loved the pilot; the gap to the reference was the primitive hull — use a real licensed model.
- **Low-poly diorama** (PolySoldier style): blocky CC0 people and props (Kenney, Quaternius), flat-shaded sets
  (desert/dusk/night), green glow for radiation, amber upper-case callouts with leader + arrow, red alarm label +
  dashed ring, tilted time cards, clocks/documents as props in the scene, whip pans with motion blur at every scene
  change, a camera that never stops. Reference kit: `tools/remotion/src/three/poly/`.
- **Free model sources:** Poly Haven, Kenney, Poly Pizza, NASA, Khronos samples, Smithsonian, Sketchfab
  (downloadable, ~300/day limit). One sidecar per model: licence, commercial use, attribution, polycount. Only
  commercial-use models in an upload; CC-BY credit in the description; check textures and node names for rips.
- Render on a GPU host when available (6.4× faster); layout stills before the full render.

## 4. Generated stills and clips (last, labelled)

- Only for what nothing above has. Pro image model, not flash; on a refusal, a new chat with reworded *composition*.
- **Consistency:** one style-bible reference on every generation; 2–5 set masters per story; every shot an img2img
  edit of its master; faceless or mannequin people; one character description repeated verbatim; a separate 9:16
  generation instead of cropping 16:9.
- **Defect-check every image in pixels** (`~/.claude/skills/video-craft/references/review.md` § Pixel defects); no text
  from the image model — labels come from the renderer.
- Label illustrations on screen ("illustrative reconstruction"). Video generation costs money/quota (Veo ≈ 2 clips
  per account per day at 1280×720): ask before spending, buy the cheap still first, retry single failures.
- Stylised people need no AI-disclosure label; a photoreal real person or event does.

## Consistency within a video

People keep one look for the whole video (mannequin stays mannequin); evidence/documents may switch to another look
with no person in those shots. Spell out object details that drift (a ship's rig mast by mast). Leave background
people out of close-ups (they drift to real skin).
