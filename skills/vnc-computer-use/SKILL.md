---
name: vnc-computer-use
description: Gives Claude GUI "computer use" (see the screen, click, type into desktop apps) on Linux and Windows, where native computer-use is unavailable, by mirroring the user's real desktop over VNC and driving its noVNC web client through claude-in-chrome. Use this ONLY when the target is genuinely outside a web page — native OS file pickers, desktop applications, OS/desktop settings, installers, Chrome's own settings/extension UI, or a site that blocks CDP automation. Trigger on requests like "control my desktop", "click this desktop app", "computer use on Linux", "use my signed-in Chrome", "open a GUI app and drive it", "automate a native file dialog", or when a browser-only attempt has already hit a native dialog and stalled.
---

# Computer use via VNC (Linux / Windows)

macOS has native computer-use. Linux and Windows don't — but they do have
`claude-in-chrome`. This skill bridges the gap: mirror a desktop over VNC, serve
it to a browser with noVNC, and drive that page with the `computer` tool. The
browser becomes the screen; clicks and keystrokes land on a real desktop.

## Escalate in this order — stop at the first that works

1. **Native `claude-in-chrome`.** Anything inside a web page: reading, clicking,
   forms, navigation, console/network debugging. Faster and more reliable, and
   it gives you the DOM (`read_page`, `find`, `form_input`) instead of pixels.
   Most requests end here.
2. **Native computer-use**, if the platform has it (macOS at time of writing).
   Never build this bridge on top of a capability that already exists.
3. **This skill**, only for what the browser can't reach: native file pickers
   and save dialogs, `chrome://` settings and extension UI, desktop
   applications, OS/desktop settings, installers, or a site that blocks
   CDP-based automation.

## Choosing the mode — decide, don't default

Pass the mode explicitly. One question settles it:

**Does the task need *this user's* identity, state, or windows?**

**Yes → `real` (`:0`).** Signed-in Chrome, their open windows, their desktop
settings, a document already open in an app, a site that only works while logged
in. This is a completely legitimate use — it's what the skill exists for, and
you should not hesitate or hedge about it when the task genuinely calls for it.

**No → `virtual` (`:1`).** Trying out a GUI app, driving an installer, testing
something in a browser you *want* signed out. Prefer this whenever it's
sufficient, because sharing the user's session is disruptive: you move the
pointer they're using, you steal window focus, and anything you click lands in
their live environment. Don't take over someone's screen to do work that a
scratch desktop could have done.

What you cannot do is fake the middle ground. A fresh Chrome on `:1` has no
cookies and no logins, and you can't point it at the user's profile — a running
Chrome holds a `SingletonLock` on its `--user-data-dir`, so a second instance
either refuses to start or just opens a tab in the existing one on `:0`.
Copying the profile gives a stale snapshot and still none of their windows.

```bash
ls ~/.config/google-chrome/SingletonLock   # present => profile is in use
```

So if the task needs a signed-in browser, it needs `real`. Say so plainly and
use it, rather than quietly delivering something signed-out that doesn't do the
job.

When you do use `real`, be a considerate guest: tell the user you're driving
their session, ask them to keep hands off the mouse while you work, and stop the
server when you're done.

## Start

```bash
sudo apt-get install -y tigervnc-scraping-server novnc websockify   # real mode
sudo apt-get install -y tigervnc-standalone-server novnc websockify openbox  # virtual mode

~/.claude/skills/vnc-computer-use/scripts/vnc-desktop.sh start real
~/.claude/skills/vnc-computer-use/scripts/vnc-desktop.sh start virtual
```

`real` is the bare `start` default because it's the common case for this skill,
but name the mode anyway — it keeps the choice deliberate and readable.

It prints the URL and verifies the RFB handshake before claiming success.
`stop`, `restart`, `status` behave as expected. Stop it when you're done — this
leaves an unauthenticated view of the user's screen listening on localhost.

Use `x0vncserver` (TigerVNC), not `x11vnc`: on Ubuntu 25.04 `x11vnc` logs
`screen setup finished`, then spins at 100% CPU and never sends the RFB banner.

Open it, and note the `resize` parameter differs per mode:

- **real:** `?autoconnect=1&resize=scale&reconnect=1` — scales the view in the
  browser. Never `resize=remote` here; that would change the user's actual
  screen resolution.
- **virtual:** `?autoconnect=1&resize=remote&reconnect=1` — resizes the headless
  desktop to match the canvas, giving an exact 1:1 mapping.

## Screenshots come back blank — read this before debugging

Chrome does not composite background tabs. `computer → screenshot` returns a
blank dark rectangle while the canvas holds a perfectly good image, and
`document.visibilityState` reads `"hidden"`. Nothing looks broken, which is what
makes it expensive.

Input is unaffected — clicks and typing land correctly while you see nothing.
Only painting is throttled.

Fix: mirror the canvas into an `<img>`, which rasters through the normal DOM
path. Run this with `javascript_tool` immediately before every screenshot:

```js
const c=document.querySelector('canvas'), r=c.getBoundingClientRect();
let m=document.getElementById('__vncmirror');
if(!m){m=document.createElement('img');m.id='__vncmirror';
  Object.assign(m.style,{position:'fixed',zIndex:'99999',pointerEvents:'none'});
  document.body.appendChild(m);}
Object.assign(m.style,{left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px'});
m.src=c.toDataURL('image/png');
```

`pointerEvents:'none'` lets clicks reach the canvas underneath. Anchoring to the
canvas's `getBoundingClientRect()` — not the viewport — is what keeps what you
see aligned with what you click, because in `scale` mode the canvas is
letterboxed inside the viewport.

The loop is **refresh mirror → screenshot → act**. A stale mirror looks exactly
like "my click did nothing" and sends you debugging the wrong layer.

## Clicking: just click what you see

With the mirror anchored to the canvas rect, the transforms cancel out and
screenshot coordinates land correctly. Verified on a 3840x1080 desktop: a hover
aimed at screenshot `(1200,300)` landed on desktop `(2939,339)`, matching
prediction exactly.

You rarely need the math, but when a click seems misplaced this is how to check
it. The `computer` tool scales your coordinates from screenshot space to CSS
viewport pixels by `viewport_width / screenshot_width`; noVNC then maps the
viewport onto the canvas:

```
s        = viewport_w / screenshot_w          # e.g. 1910/1568 = 1.2181
clientX  = sent_x * s
desktopX = (clientX - rect.left) * canvas.width  / rect.width
desktopY = (clientY - rect.top ) * canvas.height / rect.height
```

Read the live values rather than assuming them — `rect` changes whenever the
browser window resizes:

```js
const c=document.querySelector('canvas'), r=c.getBoundingClientRect();
JSON.stringify({rect:r.toJSON(), buf:[c.width,c.height], vp:[innerWidth,innerHeight]})
```

## You share one pointer with the user

In `real` mode there is no separate input channel — you and the user drive the
same X pointer. If they touch the mouse mid-task your click lands somewhere
else, and any calibration you measure becomes garbage. This is inherent, not a
bug to fix.

So: tell the user to keep hands off while you work, and verify effects
out-of-band rather than trusting that a click did what you intended.

```bash
DISPLAY=:0 xdotool getmouselocation                 # where did it actually land?
DISPLAY=:0 xdotool getactivewindow getwindowname    # did focus change?
```

Symptom to recognise: measurements that contradict each other — two calibration
samples implying a *negative* scale, say — mean the pointer was moved by someone
else, not that your model is wrong. Re-measure instead of "correcting" a formula
that was already right.

Because clicks are contested and land on the user's real session, treat
irreversible controls (send, delete, purchase, confirm) as needing explicit
confirmation, exactly as you would in a browser.

## Driving the virtual desktop

Only relevant in `virtual` mode. Launch apps directly rather than hunting for
icons:

```bash
DISPLAY=:1 xterm &
```

Verify by window list, not by guessed process name — `x-terminal-emulator` may
resolve to something else entirely (`terminator` here), so `pgrep xterm` can
report nothing while the app is running fine:

```bash
DISPLAY=:1 xwininfo -root -children
```

## Security

No VNC password is used, so both ports bind `127.0.0.1` only. This matters:
`websockify` binds `0.0.0.0` by default, which would expose an unauthenticated
desktop to the LAN. Keep the localhost binding; don't expose it to a network
address.

## Windows

Same architecture, different server, and **not verified** — see
`references/windows.md` and say it's untested if you use it.

## More

- `references/troubleshooting.md` — blank screenshots, screenshot timeouts,
  canvas stuck at 0x0, dead handshake vs dead paint.
- `references/real-display.md` — detail on real-session mode and calibration.
