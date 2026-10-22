# Voice, pronunciation and bilingual cuts

Read `../SKILL.md` first; the generic TTS/caption mechanics are in
`~/.claude/skills/video-craft/references/remotion.md` § Voice and captions. Reference kit:
`<story-repo>/projects/youtube-stories/CLAUDE.md` rules 8–9, `tools/README.md` (v2.10, v2.13, v2.18,
v2.19), `tools/diacritize.py`, `tools/pron_sheet.py`, `tools/pronounce.yaml`, devlogs
`claude_2026-10-16-khaled-revoice-pilot.md` and `claude_2026-10-22-pronunciation-audit.md`.

## Choosing and locking the narrator

- **Audition by ear across the whole voice pool, not by accent label**: the winning Gulf-market voice was tagged
  Levantine. Test on real script beats with names, numbers and dates, not a one-line hook.
- **Lock one voice per channel** and record it in every sidecar (so retention can be compared per voice). Never mix
  voices inside a video.
- **What worked:** ElevenLabs `eleven_v3`, default settings (stability 0.5, similarity 0.8, style 0, speaker boost),
  no accent tag, calm "documentary friend" register. Cheaper TTS (OpenAI `gpt-4o-mini-tts`) was fine for drafts but
  the owner rejected its quality once sped up.
- **Speed 1.1–1.4×, never above 1.5×**, pitch-kept, picked per episode so ASR stays clean and it doesn't sound rushed
  (1.2 ≈ 12 Arabic chars/s; English premade voice at 1.15).
- **Emotion tags** (`[urgent]`, `[softly]`) steer `eleven_v3` and aren't spoken; `[whispers]` slurred words even at 1.0
  — use `[softly]`.

## Takes, cost and caching

- One TTS call per beat; cache by hash of (provider, voice, model, settings, text); **always render with reuse** —
  without it every take re-bills and comes back a different length.
- Log the billed cost per take (ElevenLabs returns a `character-cost` header ≈ 0.22 × characters on `eleven_v3`
  here, ~175 per 800-char episode). Budget the quota before running parallel agents on one key: it hit 0 mid-batch.
- Voice everything in one pass first, then render with reuse only.
- Free fixes: keep TTS text separate from caption text (`pronounce:` map) so caption edits don't re-bill; splice a
  word from an already-billed take at a measured silence.

## Every word spoken, and the right word

1. **ASR every take** (Groq whisper-large-v3 was the most faithful; gpt-4o-transcribe "corrected" toward the standard
   language). Fail any word both transcribers heard before a re-roll and neither hears after.
2. **Last words and post-ellipsis words get dropped**: no ellipsis before a payoff; start a take with a short filler.
3. **Homographs are invisible to ASR** (shadda/vowel differences: Arabic مسلم *muslim* vs *musallim*, مية *water* vs
   *hundred*, عالم, ملك, قتلت, ولد, شعر, سكّر; English *read*, *lead*, *live*). Detect: clip the word ± one word and ask
   an audio model for an open-ended Latin romanization ×3 (never "A or B?"); retry refusals; it scored 4/4 on the
   known bad take and 3/3 on the fix. A clip cut on bad word times gives nonsense — check the window.
4. **Fix with the lightest touch:** reword first; else mark only the disambiguating letters (never full
   diacritisation: 42% slower, sounds formal); phrase keys when both senses occur in one script. Keep a fix only on
   PASS (about half pass; a re-voice is a new random roll that can make another word worse).
5. **The owner picks by ear:** a sheet of variants of the *real* line (current take, marked spellings, speeds via
   atempo at zero cost, settings variants) with review sidecars; only an approved pick enters the **shared lexicon**
   applied to every episode. A new lexicon key re-bills every take containing it on that episode's next render.
6. **Transliterate brand and place names, never translate them**; check every real-world name you put in a script.

## Bilingual cuts from one spec

- One builder script, every on-screen string an `(lang1, lang2)` pair, both specs written together; the props carry
  the same shot fractions; only beat lengths differ. Abort the render script if the builder fails (a syntax error
  once rendered the previous specs silently).
- Per-language identity: voice and speed, caption style (karaoke is RTL-specific; the English cut used bare 2–3-word
  white lines with a stroke, no pill), font and digits, title grammar, punctuation (no Arabic punctuation in the
  English `.srt`), a separate upload record and channel.
- Run the critic on each language: it catches different things (timing in shorter shots, punctuation, wording too
  close to a reference's title).
