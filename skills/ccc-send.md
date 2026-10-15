# CCC Send - File Transfer Skill

## Description

Send files to the user via Telegram using the ccc send command.

## Usage

When the user asks you to send them a file, or when you have generated/built a file that the user needs (like an APK, binary, or any other file), use this command:

```bash
ccc send <file_path>
```

## How it works

- **Small files (< 50MB)**: Sent directly via Telegram
- **Large files (≥ 50MB)**: Streamed via relay server with a one-time download link

## Examples

### Send a built APK

```bash
ccc send ./build/app.apk
```

### Send a generated file

```bash
ccc send ./output/report.pdf
```

### Send from subdirectory

```bash
ccc send ~/Downloads/large-file.zip
```

## Important Notes

- The command detects the current session from your working directory
- For large files, the command will wait up to 10 minutes for the user to download
- Each download link is one-time use only
- Use this proactively when you've created files the user needs!
