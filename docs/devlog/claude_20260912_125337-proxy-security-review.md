# Claude proxy comparison and safe setup review

Review date: 2026-09-12. Scope: inspect two upstream projects and recommend a safe setup on this Apple Silicon Mac. No installation or authentication was performed.

## Evidence

- Raine source: commit [`bcfa0a401a6bfe0eea278c65edecfcedaad919c4`](https://github.com/raine/claude-code-proxy/tree/bcfa0a401a6bfe0eea278c65edecfcedaad919c4), package/release v0.1.39. Snapshot: `/tmp/ccp-security-review-20260912`.
- Fcakyon source: commit [`2c34184e910e9de2e302f16b6d8f9c0e68c91a48`](https://github.com/fcakyon/claude-code-with-codex/tree/2c34184e910e9de2e302f16b6d8f9c0e68c91a48), package v0.3.1. Snapshot: `/tmp/audit-fcakyon-20260912`.
- Both complete `scripts/install.sh` files were read, with targeted review of credentials, server routes, logging, configuration, manifests, and release workflows. Both passed `bash -n`; installers were not executed.
- Raine v0.1.39 installer and `src/auth.rs` matched the reviewed main snapshot byte-for-byte via `diff`.
- Downloaded Raine v0.1.39 darwin-arm64 archive: SHA-256 `77b89c95adb798785d9a681f9e30384187023dd8f179b9600c4f5a47f26edaaf`, matching GitHub release asset digest and current Homebrew formula. Archive listed only `claude-code-proxy`.
- Extracted binary in `/tmp/ccp-review-binary`: `file` identifies Mach-O arm64; `codesign --verify --strict` passes. Signature is ad-hoc/linker-signed, with no Apple developer TeamIdentifier. Binary was not run or re-signed.
- Local readiness: Claude, Codex, Homebrew, and Rust tools exist. Existing native Codex auth file has mode 0600; contents were not read. No proxy config directory found, no matching proxy setup references in checked shell files/Claude settings/LaunchAgents. No port 18765 listener returned by `lsof`; it emitted an unrelated inaccessible network-volume warning, so this is preliminary rather than conclusive port verification.

## Recommendation

Choose Raine for a separate Claude Code session backed by Codex. Fcakyon is a fork adding native Anthropic passthrough and switching between Claude and Codex within one conversation; its extra integration is useful specifically for that requirement. Raine avoids the fork's default shared native Codex credential write path.

This is a focused static review and release-integrity check, not a complete dependency audit, reproducible-build verification, malware certification, or authenticated functional test.

## Installer findings

Sources: [Raine installer](https://github.com/raine/claude-code-proxy/blob/bcfa0a401a6bfe0eea278c65edecfcedaad919c4/scripts/install.sh), [Fcakyon installer](https://github.com/fcakyon/claude-code-with-codex/blob/2c34184e910e9de2e302f16b6d8f9c0e68c91a48/scripts/install.sh).

Both download a release archive and same-release checksum, extract, copy/overwrite the executable, and run it to check its version. Both can invoke sudo for an unwritable destination. Both remove the target binary's macOS quarantine attribute, remove its existing signature, and ad-hoc sign it. These actions affect the executable, not system-wide Gatekeeper configuration. Neither installer reboots, restarts Docker, kills processes, registers autostart, or edits shell/Claude settings. Cleanup uses a quoted mktemp directory.

Checksums protect against corruption but are not independent publisher authentication. Both scripts can skip checksum verification if neither supported tool exists while still reporting success. This Mac has `shasum`. Avoid piping a mutable remote script into a shell.

The reviewed [Homebrew formula](https://github.com/raine/homebrew-claude-code-proxy/blob/main/Formula/claude-code-proxy.rb) installs a versioned release with SHA-256 and only calls `bin.install` in its install method. It defines an optional service, which is not an instruction to enable it. Formula contents can change and must be rechecked at install time. Its test block contains an escaped Ruby interpolation, so perform a direct executable version check rather than relying solely on that test.

## Runtime findings

- Both bind to loopback by default and lack inbound client authentication. A dummy `ANTHROPIC_AUTH_TOKEN` is not access control. Other processes/users on the machine may reach the local API and consume provider quota. Keep explicit loopback binding and run only during use.
- Raine owns separate provider credentials. Its docs claim Keychain storage, but reviewed [`src/auth.rs`](https://github.com/raine/claude-code-proxy/blob/bcfa0a401a6bfe0eea278c65edecfcedaad919c4/src/auth.rs#L65) rejects Keychain writes and falls back to files. File saves set directory mode 0700 and file mode 0600. Treat `~/.config/claude-code-proxy/codex/auth.json` as a secret; do not promise Keychain-backed storage.
- Fcakyon refreshes and rewrites native Codex credentials by default. Atomic replacement does not serialize refreshes against another Codex process. [`CCP_CODEX_AUTH_FILE`](https://github.com/fcakyon/claude-code-with-codex/blob/2c34184e910e9de2e302f16b6d8f9c0e68c91a48/src/providers/codex/auth/token_store.rs#L123) supports another path, but a copied live refresh token does not constitute independent authorization.
- Full traffic capture is opt-in and contains prompts/code/tool content even with header redaction. Avoid debug helpers, which enable capture. Default error logs can still contain sensitive response content. See [Raine storage reference](https://github.com/raine/claude-code-proxy/blob/bcfa0a401a6bfe0eea278c65edecfcedaad919c4/docs/src/content/docs/reference/files-and-storage.md).
- The proxy receives conversation content and forwards it to the chosen provider. Fcakyon's Claude route additionally sees Claude's forwarded subscription credential; its README says it does not store that credential.
- Raine also reroutes recognized Claude Bash security-classifier requests to a Codex model; retain explicit tool approvals for initial testing rather than assuming equivalent automated approval behavior. See [`src/server.rs`](https://github.com/raine/claude-code-proxy/blob/bcfa0a401a6bfe0eea278c65edecfcedaad919c4/src/server.rs#L55).
- Both are unofficial integrations. Provider access/account enforcement remains outside the projects' control; Raine explicitly notes this in its README.

## Concrete setup plan

1. Install the inspected version via a rechecked Homebrew formula and pin it, or place the checksum-verified binary in a dedicated versioned user-owned directory. Do not execute either stock installer. Do not strip quarantine/signatures if macOS blocks execution; investigate the specific block.
2. Use Raine's own fresh `codex auth login` flow. Do not copy, overwrite, or refresh the existing native Codex auth file. Verify actual credential location and restrictive permissions without printing token contents.
3. Start manually in the foreground with `CCP_BIND_ADDRESS=127.0.0.1`, `CCP_TRAFFIC_LOG=0`, and port 18765 after checking availability. Ensure inherited endpoint overrides are absent or intentional. Leave verbose logging unset. Do not enable a Homebrew service for the trial.
4. Launch a separate Claude process with process-scoped `ANTHROPIC_BASE_URL=http://127.0.0.1:18765`, dummy `ANTHROPIC_AUTH_TOKEN=unused`, a model from the proxy's catalog, and the upstream documented nonessential-traffic/nonstreaming-fallback controls. Preserve ordinary Claude settings and permission prompts. See [client configuration](https://github.com/raine/claude-code-proxy/blob/bcfa0a401a6bfe0eea278c65edecfcedaad919c4/docs/src/content/docs/using/configure-claude-code.md).
5. Verify executable version, loopback listener, `/healthz`, model listing, then a harmless prompt and one explicitly approved read-only tool action in a nonsensitive directory. Confirm normal Claude and native Codex still work independently.
6. End foreground sessions with Ctrl-C. Without global settings or service registration, normal launches retain their previous behavior. Remove only individually inspected installation/state paths if later uninstalling; retained credentials require a deliberate logout/removal.

No global settings, credentials, services, security controls, or existing processes were changed. Downloaded review artifacts were retained. No commit was made. The referenced private `~/.Codex/Codex.local.md` file was absent; the available migrated private instructions were read.
