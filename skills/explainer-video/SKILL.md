---
name: explainer-video
description: Make a narrated explainer video about code, a system or a pull request with Remotion, AI voice-over and subtitles. Use when asked for an explainer, walkthrough or "video that explains X".
---

# Explainer videos

A simple recipe for a narrated explainer video: script → voice → scenes in Remotion → render.

## Steps

1. **Understand the topic.** Read the code, PR or docs you are explaining and list the 3–6 points worth showing.
2. **Script.** Write the narration as JSON, one entry per scene. Keep it short: ~150 words per minute of video.
3. **Voice-over:**
   1. OpenAI `gpt-4o-mini-tts` per scene, through **Doomscroll** first. It is an OpenAI-compatible, credit-metered
      proxy, so no OpenAI key is needed. Use the OpenAI SDK with `base_url="https://doomscroll.build/api/agent/v1"`
      and the Doomscroll key as `api_key`. Load the key inside the script, never print it. Look first in
      `DOOMSCROLL_API_KEY`, else in `~/.config/doomscroll/credentials.json` → `["https://doomscroll.build"]["apiKey"]`,
      which the Doomscroll agent client's `doomscroll.mjs login` saves after a browser approval.
      - Fallback: with no Doomscroll sign-in, use the user's own `OPENAI_API_KEY` against OpenAI directly.
      - With neither, ask the user to sign in at doomscroll.build → Settings → Agent access, or to give an OpenAI key.
      - A 402 from Doomscroll means out of credits. Keep one voice provider per video.
   2. Transcribe each clip with `whisper-1` to get timings for the subtitles.
4. **Scenes.** Create a Remotion project (`npx create-video@latest`), one composition per scene, with the scene's
   audio and a simple diagram, code snippet or bullet list. Use the `remotion-best-practices` skill for Remotion help.
5. **Render** with `npx remotion render`, then check the output with `ffprobe` (size, duration, audio stream).
6. **Deliver** the mp4 with burned-in subtitles and an `.srt` file.
