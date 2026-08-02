# Windows

**Unverified.** Everything below is the Linux architecture mapped onto Windows
components. It was not tested — the verification for this skill was done on
Ubuntu 25.04. Treat this as a plan to validate, and tell the user it's untested
if you use it.

## Architecture

Identical in shape to Linux; only the VNC server changes:

```
VNC server (real Windows desktop)  →  websockify  →  noVNC in Chrome  →  computer tool
```

Windows has no equivalent of a spare headless X display, so there is no
isolated virtual-desktop mode. You are mirroring the user's actual session,
which means **all the cautions in `real-display.md` apply** — shared pointer,
scaled canvas, calibrate-don't-derive, get explicit permission first.

## Components to try

- **VNC server** — TightVNC or UltraVNC, both of which install as services and
  can bind to localhost. Configure a loopback-only listener.
- **websockify** — `pip install websockify`, or the bundled binary in a noVNC
  release.
- **noVNC** — download a release and point websockify's `--web` at its folder.

Roughly:

```powershell
websockify --web=C:\path\to\noVNC 127.0.0.1:6080 localhost:5900
```

Then open
`http://localhost:6080/vnc.html?autoconnect=1&resize=scale&reconnect=1`
and use the mirror snippet from SKILL.md.

Use `resize=scale`, not `resize=remote` — as on any real display, `remote`
would try to change the user's actual screen resolution.

## Things to check when validating

- Whether the server binds loopback-only by default, or needs to be told. A
  no-auth VNC server reachable on the network is the main risk here; if the
  server can't be made passwordless *and* localhost-only, set a password and
  have noVNC prompt for it rather than exposing an open port.
- Whether UAC prompts are visible at all. UAC runs on the secure desktop, which
  many VNC servers cannot capture — expect a black screen there. This is a
  genuine capability limit, not a bug to debug.
- The screenshot/blank-canvas behaviour should be identical, since it's a
  Chrome compositing property rather than an OS one. The mirror snippet should
  apply unchanged.
- No `xdotool` equivalent, so the out-of-band "where did my click actually
  land?" check needs a substitute — PowerShell can read the cursor position:
  ```powershell
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.Cursor]::Position
  ```
  That gives you the calibration loop described in `real-display.md`.
