# Move tcc and friends into dotclaude

`cc`, `tcc`, `_tagent`, `tcodex`, `topencode`, `tcca`, `tls`, `tmux-restore`
and their helpers (`_claude_argv`, `_color256_to_hex`, `_set_vscode_color`)
moved verbatim from the dotfiles' `.bash_aliases` to `scripts/claude-shell.sh`.

- `.bash_aliases` sources it only if the file exists, right after `_bidi`.
  `_bidi` stays in dotfiles because `tw` uses it; `claude-shell.sh` falls back
  to running the command as-is when `_bidi` is missing.
- One comment example named an employer directory; it now says `acme.d`.
- `tests/claude_shortcuts_test.py` and `tests/tmux_restore_launcher_test.py`
  moved here and read `scripts/claude-shell.sh`. `!/tests/` is whitelisted.

Verified: `type tcc cc tmux-restore tls` resolves to this file in bash and zsh,
`uv run --offline --with pytest pytest tests/` gives 28 passed, the dotfiles
suite gives 54 passed, and `install-tmux-stack.sh --check` reports
"tmux-restore available".
