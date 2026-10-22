# Remotion: building, timing, mixing and rendering

Shared by every video skill. Read `../SKILL.md` first for the craft rules this implements. For Remotion API details,
use the installed official skills through `remotion-best-practices` (create, captions, markup, render, maps, 3d).

Reference implementation (plain paths, read when useful):
`<story-repo>/projects/youtube-stories/tools/remotion/README.md` (compositions, props, traps) and its
`src/` (`Explainer3D.tsx`, `three/`, `three/poly/`, `AnimatedMap.tsx`, `Timeline.tsx`, `Counter.tsx`, `BarChart.tsx`,
`CameraObscura.tsx`, `ElephantClock.tsx`), `scripts/render_many.mjs`, `scripts/stills.mjs`, and
`../render_on_gpu.sh`. Sources: devlogs `claude_2026-10-14-ep09-ep10-motion-pass.md`, `claude_2026-10-19-motion-taste-skills.md`,
`claude_2026-10-21-3d-explainer-pilot.md`, `claude_2026-10-21-gpu-render-llm.md`,
`claude_2026-10-22-polysoldier-format.md` in `<story-repo>/docs/devlog/`.

## Setup

If `remotion-best-practices` isn't among the available skills, install Remotion's official skills
(<https://github.com/remotion-dev/skills>), then read the ones that apply:

```bash
npx -y skills add remotion-dev/skills --global --skill '*' --agent claude-code --yes
```

Drop `--global` to install into the current project. `npx -y skills add remotion-dev/skills --list` shows what ships.

- `npx`/`npm` must be the real Node binaries, not a bun shim.
- No system `ffmpeg`/`ffprobe`: use `node_modules/.bin/remotion ffmpeg|ffprobe` (lacks some filters, e.g.
  `volumedetect`).
- Pin the Remotion version across all `@remotion/*` packages; one mismatched package breaks the bundle.

## Composition structure

- **One composition per scene/shot**, so one can be re-rendered alone; a parent composition (or an ffmpeg concat)
  stitches them. Props carry everything a shot needs; nothing reads global state.
- **`defaultProps` leak into renders.** Remotion merges them *under* input props, so a demo value shows up in a real
  shot that omits that key (a demo counter appeared on an unrelated map). Apply demo defaults only in Studio (e.g.
  only when a `meta` prop is absent), and preview a still of every shot.
- **Author timing as fractions of the shot (0..1), not seconds.** The shot length follows the voice; fractions keep
  the choreography's shape when a re-voice changes the length. A build script converts word times → fractions.
- **Every file added under `src/` changes the bundle hash**, so any cache keyed on it re-renders every shot once.
- **JSX text can't contain a bare `<`** (`< 1 min`); wrap it in `{"…"}`.
- **YAML parses a key named `off`/`on`/`yes` as a boolean**; quote it.
- **Every frame must render alone** [gittok/doomscroll, 2026-10-22]: compute state at frame N from props and N
  (replay events up to N), never from what earlier frames did, so stills, GIF previews and seeks are correct.
- **Validate an LLM-written storyboard with a schema** (zod) before rendering, with one tool-less retry on failure;
  reject only runaway text (e.g. > 26 words in a beat), not style [gittok/doomscroll, 2026-10-22].

## Motion that settles

- **Ease-out with a pace knob:** `p' = 1-(1-p)^(1+pace)`, pace 2 by default (fast start, settles). Camera flies take
  `1/pace` of their keyframe gap and land on a stiff spring with ~2% overshoot (a punch-in). Draw-ons run in half the
  time. Never default a new piece to pace 1.
- **Pops:** `spring({damping ~11, stiffness ~170})` or outBack with ~6% overshoot; leader line first, then text.
- **Stagger related elements 60–80 ms apart, < 500 ms total** (card → accent bar → number → label), land with a
  2-frame squash then a damped pop, add a ~3% ambient push on any hold. A synced single fade and a frozen hold are
  what read as "PowerPoint". The `motion-design` skill is a good review checklist for this.
- **Whip transition:** ~0.2–0.3 s, ~38° camera yaw (or a fast pan on 2D) plus a directional blur up to ~70 px; it
  hides the hard cut and is the cheapest way to raise perceived cut rate. Use it at scene changes and the loop seam.
- **Ship taste changes opt-in behind a prop**, with the prop absent byte-identical (`ffmpeg -f framemd5`), so old
  renders don't silently change.
- **Counters:** land the count *before* the spoken number (mid-count frames show wrong digits); hold the final value
  with a separate static card starting exactly where the count ends, or it blinks.

## Voice and captions

0. **Where the voice comes from:** Doomscroll (doomscroll.build) is an OpenAI-compatible, credit-metered voice proxy.
   Point the OpenAI SDK at `https://doomscroll.build/api/agent/v1` with the Doomscroll key, which comes from
   `DOOMSCROLL_API_KEY` or `~/.config/doomscroll/credentials.json` (saved by `doomscroll.mjs login`).
   `audio.speech` and `audio.transcriptions` (whisper-1 word timestamps) then work unchanged, and no provider key is
   needed. Your own `OPENAI_API_KEY` is the fallback. Pick one provider per video and keep it for every take.
1. **One TTS call per beat/scene.** Measure the trimmed take; that length is the cut length.
2. **Trim tails with a real threshold:** scan with `silencedetect` at −35 dB; a −44 dB breath tail survived a −45 dB
   trim and became 2.5 s of dead air.
3. **Word timestamps from ASR, aligned back to the script words with difflib**, so captions show the exact script, not
   the ASR spelling. Groq whisper-large-v3 was the most faithful; gpt-4o-transcribe "corrects" toward the standard
   language and garbled whole takes. Handle 429/401 with backoff and fail loudly: a silent fallback to
   character-proportional timing once shipped mistimed captions.
4. **Reject truncated takes:** < ~250 ms per word means the API cut the audio. Also check the final words exist in the
   ASR (TTS drops words after an ellipsis and at take edges; start a take with a short filler word if needed).
5. **Speed up in post only:** pitch-kept `atempo`, then scale caption times by the same factor. Some TTS APIs ignore a
   `speed` parameter and "speak fast" instructions (measured 9.3 → 9.4 chars/s). Cap long pauses (e.g. > 0.35 s →
   0.35 s) with `silenceremove stop_periods=-1:stop_duration=0.35` (adding `stop_silence` disables the shortening).
6. **One voice per video.** If the main TTS provider fails, voice the whole video with the fallback; never mix two
   voices [gittok/doomscroll, 2026-10-22].
7. **Cache takes by hash of (provider, voice, model, settings, text)** and re-render with "reuse" always. Changing the
   instructions text or a pronunciation key changes the hash and re-bills; a re-roll is a new random take that can
   make another word worse. Keep the TTS text separate from the caption text (a `pronounce:` map) so caption edits
   never re-bill.
8. **Cue hook:** `useCue()("phrase")` returns the frame a phrase is spoken and throws if it isn't in the narration;
   an overlay timed to a word that falls outside its shot must fail the build, never silently not draw.
9. **Never reuse one caption box across beats**: split each beat's text into word chunks timed from that beat's TTS
   duration/word times [gittok/doomscroll, 2026-10-22]. **CJK counts double width** when sizing a line; **RTL/Arabic**
   needs HarfBuzz/raqm shaping (or the browser's), a right-to-left word order in karaoke, and no letter-spacing.
10. **Caption chunks:** 2–5 words, one line, never a 1-word orphan, never split a proper noun or end on a preposition,
   strip trailing commas/colons, a multi-word number lights as one unit, current word highlighted (e.g. #FFD400,
   ×1.06 scale, chunk pops .85 → 1 over 4 frames). Hide captions under a hook pill instead of stacking them.
11. **Typed-on text runs ~55 ms/char** — a 25-char stamp needs 1.4 s, so on 1.3–2 s cuts use instant or 25–30 ms.

## Audio mix and loudness

- **Targets:** integrated −14 to −16 LUFS (we ship ~−15), true peak ≤ −1 dBTP (we land −3 to −4), the bed 12–20 dB
  under the voice. Measure with `ffmpeg -i out.mp4 -af ebur128=peak=true -f null -`.
- **Measure the bed under the voice, don't trust the volume number.** A −30 LUFS bed at 0.35 volume with ratio-8
  ducking ended ~46 LUFS — inaudible (~28 dB under). Our working setting: volume 0.8 with ducking, or no duck at 0.5,
  to land ~20 dB under.
- **Two-pass loudnorm** (measure, then apply) or a final gain trim; single-pass landed 1 dB off.
- **Fades:** ~0.25 s in, ~0.4 s out, so music carries through a loop seam.
- **One bed per video**, different instrument family per video; licence sidecar with every music/SFX file. Drop the
  source audio of footage unless it is the point.
- **Whispered takes can measure louder** than normal ones; measure, don't assume.

## 3D scenes with `@remotion/three`

- **Deterministic per frame:** drive the camera and every animated value from `useCurrentFrame()` in
  `useLayoutEffect`, never R3F `useFrame`. Put all scene state in one pure `simulate(props, frame)` returning camera,
  poses, events and named anchors; both the WebGL scene and the HTML overlay read it, so labels never drift.
- **Labels:** project world anchors to pixels (`vector.project(camera)`) and draw labels as HTML/SVG over the canvas.
  9:16 at a 40° vertical fov is only ~23° wide: frame for it.
- **Mechanism events are props** (`partOff`, `eject{slow}`, `chute`), with a slow-motion window on the key moment.
  Draw a part before its label appears; cap travel so it stays in later shots.
- **X-ray/ghost look:** ~14% opacity body, bright edges via `EdgesGeometry` (threshold ~28° on primitives, ~42° on
  tessellated glTF, or it scribbles), solid internals.
- **glTF:** load with three's `GLTFLoader`, bake once into metres scaled to a sourced real dimension, inspect the node
  tree before trusting a brief, `toCreasedNormals` (~36°) on faceted hulls. Copy assets into `public/` (symlinks
  arrive dangling after rsync). Hold the frame with `delayRender` and mount `ThreeCanvas` only after every model has
  loaded: with `frameloop: never`, a mesh that loads after mount never reaches the screenshot.
- **Licences:** one sidecar per model (licence, commercial use, attribution, source URL). Only commercial-use models in
  an upload; CC-BY needs its credit line in the description. Check bundled textures (one was a watermarked photo) and
  node names (`SK_*_LOD0` = probable game rip).
- **Look:** declare fog in the R3F tree (imperative fog drew objects flat); flat tone mapping for low-poly palettes
  (ACES washed them out); software GL draws 1 px lines, so draw cords as thin cylinders; fire from puffs, not cones.
- **`hq` mode on a GPU:** soft shadow maps, `dpr 2` supersampling, an HDRI sky + image-based light (~0.12 s/frame vs
  0.08 plain). **Don't ship depth-of-field:** it blacked out ~1 frame in 5 on the GPU and renders blank in software;
  run `ffmpeg -vf blackdetect` on any 3D shot before shipping.

## Rendering WebGL on a GPU host

Optional offload. Only when the invoking skill or prompt allows rendering on another host; headless workers render
locally and write only where their prompt says.


- **GL flags:** no GPU → `--gl=swangle` (~0.2–0.5 s/frame at 1080×1920). NVIDIA host without `/dev/dri` →
  `--gl=angle-egl --chrome-mode=chrome-for-testing` (measured 0.082 s/frame on an RTX 3090, ~6.4× faster, identical
  pixels). `vulkan`, `angle` and `headless-shell` fell back to software there, and `remotion gpu` reported
  "software" even when it worked: trust measured s/frame.
- **GpuSync — the screenshot race.** On a shared GPU, Remotion captured the canvas before the GPU had finished
  drawing: objects or whole layers went missing (a shadow drawn without its object), deterministic per scene but
  shifting when unrelated objects were added. Not culling; drawing twice made it worse. Fix: a component inside the
  canvas that, in a `useEffect` after `@remotion/three` advances the frame, calls
  `gl.getContext().readPixels(0, 0, 1, 1, RGBA, UNSIGNED_BYTE, buf)` — a 1-pixel readback blocks until the frame is
  really drawn. Put it in every 3D shot.
- **Batch:** bundle once, open Chrome once, then `selectComposition` + `renderMedia` per job (a per-shot CLI render
  spent ~10 s bundling each time). A full 36-shot 3D Short: CPU ~16 min, GPU per-shot 631 s, GPU batched 524 s.
- **Retries:** "Web page caused context loss and was blocked" can kill a batch on a shared card. Fresh browser per
  job, up to 3 retries, resume by skipping outputs that already exist.
- **Shared host etiquette:** `nice -n 19`, userland only (a Node tarball, Chrome for Testing self-downloads ~191 MB),
  never touch the other tenant's job; a 1080×1920 frame needed < 1 GB VRAM. Rsync the project without
  `node_modules/.remotion`.
- **Layout check before the full render:** 3 stills per shot (`remotion still` at 0.1/0.5/0.9 of the shot) caught 10
  bad framings on the first 3D pilot in ~1–3 min. Run it from inside the project dir, or Remotion downloads ~100 MB
  of Chrome into the current directory.

## Render traps

- **Don't restart a renderer mid-render** (a dev server, a Studio, a worker); it kills or corrupts the in-flight
  render [gittok/doomscroll, 2026-10-22].
- **GIF previews ≤ 5 MiB** — GitHub's camo proxy refuses bigger images, so a PR preview silently breaks
  [gittok/doomscroll, 2026-10-22].
- Chrome dying during `remotion still/render`: look for unreadable directories on PATH and strip them.
- Memory: guard below ~1.5 GB available; concurrency 1 peaked ~1.6 GB, 2 at ~1.8 GB on a 1080×1920 render.
- Clip big GeoJSON to the map box (88k → 20k vertices cut one map render from 455 s to 68 s).
- Panels over busy footage at ~0.97 opacity; check frames every 0.5 s for label collisions.
- Stills taken mid-fade look washed out; that's the transparent PNG, not the video.
- After any change to the final concat/overlay pass, `ffprobe -count_frames`: one change silently dropped 1661 → 779
  frames. Concat can also drift an overlay by one frame.
- `while pgrep -f '<pattern>'` matches its own shell's command line and never exits; use `pgrep -a <name> | grep`.
- ffmpeg concat lists need absolute paths; never `-shortest` when video may be shorter than the voice (pad with
  `tpad` and set `-t`).
- Arabic/RTL: shape with HarfBuzz/raqm, never letter-space Arabic, check the font has every glyph (Kufi lacks Latin
  punctuation and « »), and never put ` · ` next to an Arabic-Indic digit (it reads as ٠).
