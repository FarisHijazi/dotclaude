# claude-codex startup services

On 2026-09-12, configured the installed `claude-codex` 0.3.1 binary for per-user startup on this Mac with `~/Library/LaunchAgents/local.claude-codex.plist`. It runs `serve --no-monitor --port 18765`, binds to `127.0.0.1`, disables traffic capture, uses restrictive launchd permissions, and is kept alive by launchd. `/healthz` returned `{"ok":true}` after loading the agent.

The same per-user service was configured on `dema.local` and `thmanyah.local` as `claude-codex.service` under systemd user management, with loopback binding, traffic capture disabled, restart-on-failure, and `enable --now`. Both hosts had user lingering already enabled. `thmanyah.local` was verified over its Tailscale address (`100.120.250.112`) with systemd enabled/active, loopback listener, and `/healthz` success. `dema.local` was configured while reachable on its LAN alias but is currently offline from this Mac's tailnet view, so its live state cannot be rechecked off-LAN until the host returns online.

The existing Mac foreground process was already gone before the LaunchAgent was bootstrapped; no active request was interrupted. No credentials, Claude settings, Docker services, firewall, routes, or exit-node settings were changed.
