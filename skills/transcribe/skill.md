---
name: transcribe
description: Transcribe audio files (voice notes, recordings) to text using Whisper large-v3. Use when asked to transcribe audio, voice notes, or recordings. Defaults to Arabic but supports all languages.
---

# Transcribe Audio Skill

Transcribe audio files to text using the Whisper large-v3 API. Always use the `whisper-large-v3` model.

## When to Use

Use this skill when the user asks to:
- Transcribe a voice note or audio file
- Read/understand a voice message
- Convert speech to text
- Transcribe WhatsApp voice notes
- Batch transcribe audio files in a directory

## CLI Tool

A standalone bash script is available at `~/bin/whisper-transcribe`.

### Usage

```bash
# Single file (default: Arabic)
whisper-transcribe file.ogg

# Multiple files
whisper-transcribe *.ogg

# Batch from directory
find . -name '*.ogg' | xargs whisper-transcribe

# Override language
whisper-transcribe --lang en recording.mp3

# Add context prompt for better accuracy
whisper-transcribe --prompt "real estate apartments Khobar" file.ogg
```

### Output

- Writes a `.txt` file next to each audio file (e.g. `voice.ogg` → `voice.txt`)
- Caches: skips files that already have a `.txt` transcript
- Prints transcript to stdout

### API Key

Requires an API key. Use `GROQ_API_KEY` by default. `TRANSCRIPTION_API_KEY` and `TRANSCRIPTION_API_BASE_URL` can override the provider, but the model must stay `whisper-large-v3`.

## Programmatic Usage (Python)

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

with open("voice.ogg", "rb") as f:
    result = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=f,
        language="ar",  # optional: helps accuracy
    )
print(result.text)
```

## Arabic Transcription Tips

- `whisper-large-v3` handles Saudi/Gulf Arabic dialect well
- Always use `whisper-large-v3`; do not downgrade or substitute another Whisper model
- Always set `language="ar"` explicitly — improves accuracy over auto-detect
- WhatsApp voice notes are `.ogg` (Opus codec) — Whisper accepts them directly, no format conversion needed
- Use `--prompt` with domain-specific keywords to help with jargon (e.g. "عقار شقة الخبر")
- Short clips (<5 seconds) can hallucinate; generally reliable for 10s+
- Cost depends on the provider; voice notes are usually low cost

## Supported Formats

ogg, mp3, m4a, wav, webm, mp4, mpeg, mpga, oga, flac

## If the CLI doesn't exist

Create it by running:
```bash
cat > ~/bin/whisper-transcribe << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
LANG_CODE="ar"; PROMPT=""
API_BASE_URL="${TRANSCRIPTION_API_BASE_URL:-https://api.groq.com/openai/v1}"
API_BASE_URL="${API_BASE_URL%/}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG_CODE="$2"; shift 2 ;; --prompt) PROMPT="$2"; shift 2 ;;
        --help|-h) echo "Usage: whisper-transcribe [--lang ar] [--prompt '...'] file [...]"; exit 0 ;;
        *) break ;;
    esac
done
[[ $# -eq 0 ]] && { echo "Usage: whisper-transcribe [--lang ar] file [...]" >&2; exit 1; }
if [[ -f ~/.env ]]; then
    set -a
    source ~/.env
    set +a
fi
API_KEY="${TRANSCRIPTION_API_KEY:-${GROQ_API_KEY:-}}"
[[ -z "$API_KEY" ]] && { echo "Error: GROQ_API_KEY or TRANSCRIPTION_API_KEY not set" >&2; exit 1; }
for file in "$@"; do
    [[ ! -f "$file" ]] && continue
    txt="${file%.*}.txt"
    [[ -f "$txt" ]] && { echo "=== $file (cached) ===" >&2; cat "$txt"; echo; continue; }
    echo "=== $file ===" >&2
    ARGS=(-s -X POST -H "Authorization: Bearer $API_KEY" -F "file=@$file" -F "model=whisper-large-v3" -F "language=$LANG_CODE" -F "response_format=text")
    [[ -n "$PROMPT" ]] && ARGS+=(-F "prompt=$PROMPT")
    if ! t=$(curl "${ARGS[@]}" "$API_BASE_URL/audio/transcriptions"); then
        echo "Error: curl failed for $file" >&2
        continue
    fi
    [[ -n "$t" && "$t" != *'"error"'* ]] && { echo "$t" > "$txt"; echo "$t"; } || echo "Error: $t" >&2
done
SCRIPT
chmod +x ~/bin/whisper-transcribe
```
