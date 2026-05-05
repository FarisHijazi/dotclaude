---
argument-hint: export [output_dir] | import <archive_path> [project_path] | cp <new_path>
description: Migrate conversation history — export/import between machines or copy to new path
---

# Migrate Claude Code History

Supports three subcommands based on `$ARGUMENTS`:

## Determine subcommand

Parse the first word of `$ARGUMENTS` to determine the mode:
- `export` → Export mode
- `import` → Import mode
- `cp` → Copy mode (legacy same-machine migration)
- anything else → show usage help

---

## Mode: `export [output_dir]`

Export the current project's conversation history into a portable `.tar.gz` archive that can be copied to another machine.

**Steps:**

1. Get the current working directory with `pwd` → call it `PROJECT_PATH`
2. Encode the path: replace each `/` with `-` (e.g. `/Users/foo/myproject` → `-Users-foo-myproject`) → call it `ENCODED`
3. Verify `~/.claude/projects/$ENCODED/` exists. If not, error: "No history found for this project."
4. Determine output location:
   - If second argument provided, use that as `OUTPUT_DIR`
   - Otherwise default to `./` (current directory)
5. Create a metadata file and archive:

```bash
# Create temp staging dir
EXPORT_DIR=$(mktemp -d)
ENCODED=$(pwd | tr '/' '-')
SOURCE="$HOME/.claude/projects/$ENCODED"

# Write metadata
cat > "$EXPORT_DIR/migrate-meta.json" <<EOF
{
  "original_path": "$(pwd)",
  "encoded_name": "$ENCODED",
  "exported_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hostname": "$(hostname)",
  "claude_version": "$(claude --version 2>/dev/null || echo unknown)"
}
EOF

# Copy project history
cp -a "$SOURCE" "$EXPORT_DIR/project-history"

# Also grab relevant session files that reference this project
mkdir -p "$EXPORT_DIR/sessions"
grep -rl "$(pwd)" "$HOME/.claude/sessions/" 2>/dev/null | while read f; do
  cp "$f" "$EXPORT_DIR/sessions/"
done

# Create archive
OUTPUT_DIR="${2:-.}"
ARCHIVE_NAME="claude-history-$(basename "$(pwd)")-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$OUTPUT_DIR/$ARCHIVE_NAME" -C "$EXPORT_DIR" .

# Cleanup
rm -rf "$EXPORT_DIR"

echo "Exported to: $OUTPUT_DIR/$ARCHIVE_NAME"
```

6. Tell the user:
   - The archive path
   - To copy it to the target machine and run `/migrate import <archive_path> <project_path>`

---

## Mode: `import <archive_path> [project_path]`

Import a previously exported archive into the local Claude history.

**Steps:**

1. Verify the archive file exists at the given path
2. Extract to a temp dir and read `migrate-meta.json`
3. Determine target project path:
   - If `project_path` argument provided, use that
   - Otherwise use the current working directory (`pwd`)
4. Encode the target path (same encoding: replace `/` with `-`)
5. Run the import:

```bash
ARCHIVE="$1"
TARGET_PATH="${2:-$(pwd)}"
ENCODED=$(echo "$TARGET_PATH" | tr '/' '-')
DEST="$HOME/.claude/projects/$ENCODED"

# Extract archive
IMPORT_DIR=$(mktemp -d)
tar -xzf "$ARCHIVE" -C "$IMPORT_DIR"

# Show metadata and read original path for rewriting
echo "Importing history from:"
cat "$IMPORT_DIR/migrate-meta.json" | python3 -m json.tool 2>/dev/null || cat "$IMPORT_DIR/migrate-meta.json"
ORIGINAL_PATH=$(python3 -c "import json; print(json.load(open('$IMPORT_DIR/migrate-meta.json'))['original_path'])")

# Rewrite absolute paths in all JSON/JSONL files if original != target
if [ "$ORIGINAL_PATH" != "$TARGET_PATH" ]; then
  echo "Rewriting paths: $ORIGINAL_PATH → $TARGET_PATH"
  find "$IMPORT_DIR" -type f \( -name "*.json" -o -name "*.jsonl" \) -exec \
    sed -i'' -e "s|$ORIGINAL_PATH|$TARGET_PATH|g" {} +
fi

# Copy project history (merge, don't overwrite existing)
if [ -d "$DEST" ]; then
  echo "Warning: destination already has history. Merging (existing files preserved)."
  cp -an "$IMPORT_DIR/project-history/"* "$DEST/" 2>/dev/null || cp -n "$IMPORT_DIR/project-history/"* "$DEST/"
else
  mkdir -p "$DEST"
  cp -a "$IMPORT_DIR/project-history/"* "$DEST/"
fi

# Copy session files (with path rewriting already applied)
if [ -d "$IMPORT_DIR/sessions" ] && [ "$(ls -A "$IMPORT_DIR/sessions/" 2>/dev/null)" ]; then
  cp -n "$IMPORT_DIR/sessions/"* "$HOME/.claude/sessions/" 2>/dev/null || true
fi

# Cleanup
rm -rf "$IMPORT_DIR"

echo "Imported history to: $DEST"
echo "You can now: cd $TARGET_PATH && claude --continue"
```

6. Tell the user:
   - History has been imported
   - They can `cd <project_path> && claude --continue` to resume

---

## Mode: `cp <new_path>`

Copy conversation history to a new directory on the same machine (original behavior).

```bash
uvx https://github.com/farishijazi/claude-migrate.git cp "$(pwd)" "$ARGUMENTS_AFTER_CP"
```

After running, tell the user:
1. The history has been copied
2. They can now `cd <new_path> && claude --continue` to resume

---

## Usage help (no valid subcommand)

If `$ARGUMENTS` doesn't match any mode, show:

```
Usage: /migrate <subcommand>

Subcommands:
  export [output_dir]                    Export history to portable archive (default: ./)
  import <archive> [project_path]        Import history archive (default target: pwd)
  cp <new_path>                          Copy history to new path (same machine)

Examples:
  /migrate export                        → creates claude-history-*.tar.gz in current dir
  /migrate export ~/Desktop              → exports to Desktop
  /migrate import ~/claude-history-myproject-20250505.tar.gz
  /migrate import ~/archive.tar.gz /home/user/myproject
  /migrate cp /new/location/of/project
```
