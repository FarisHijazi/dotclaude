# Real-display mode (`:0`)

Mirrors the user's live session — their signed-in applications and the windows
they already have open.

## When to use it, and when not to

Use it when the task needs *this user's* identity, state, or windows: a
signed-in Chrome, their desktop settings, a document already open somewhere. In
those cases it's exactly the right tool and there's no reason to hesitate.

Avoid it when a scratch desktop would do. Sharing the live session is
disruptive — you move the pointer they're using, steal window focus, and every
click lands in their real environment. If the task doesn't need their state,
run `virtual` instead.

## Why you can't fake the middle ground

A headless `:1` desktop is cleaner and has simpler coordinates, but apps started
there are fresh: no cookies, no logins, none of the user's windows. If the task
needs a signed-in browser, `virtual` cannot deliver it — say so and use `real`
rather than quietly handing back a signed-out result.

You also can't cheat by pointing a second Chrome at the user's profile. A
running Chrome holds `SingletonLock` in its `--user-data-dir`; a second instance
either refuses to start or hands the request to the running one on `:0`.
Copying the profile directory gives you a stale snapshot and still not their
open windows.

```bash
ls ~/.config/google-chrome/SingletonLock   # present => in use, don't bother
```

## Starting

```bash
sudo apt-get install -y tigervnc-scraping-server novnc websockify
~/.claude/skills/vnc-computer-use/scripts/vnc-desktop.sh start real
```

Use `x0vncserver`, not `x11vnc`. On Ubuntu 25.04 `x11vnc` logs `screen setup
finished` and `PORT=5900`, then spins at 100% CPU in state `R` and never sends
the RFB banner — a probe times out while TigerVNC answers `RFB 003.008`
instantly. The script probes the handshake before reporting success.

Open with **`resize=scale`**:

```
http://localhost:6081/vnc.html?autoconnect=1&resize=scale&reconnect=1
```

Never `resize=remote` against a real display — it instructs the server to
resize the desktop, i.e. changes the user's actual screen resolution.

Then apply the mirror snippet from SKILL.md and screenshot.

Tear down when finished; this is the user's real screen on an unauthenticated
port:

```bash
~/.claude/skills/vnc-computer-use/scripts/vnc-desktop.sh stop
```

## Coordinates

Clicking what you see works. With the mirror `<img>` anchored to the canvas's
`getBoundingClientRect()`, the screenshot→viewport and viewport→canvas
transforms cancel, so a screenshot coordinate maps to the desktop point drawn
there.

Verified on a 3840x1080 ultrawide in a 1910x931 viewport (canvas letterboxed to
1910x537 at top offset 197): a hover aimed at screenshot `(1200,300)` produced
`clientXY (1462,365)` and landed on desktop `(2939,339)` — exactly the predicted
value.

The chain, for when something looks wrong:

```
s        = viewport_w / screenshot_w
clientX  = sent_x * s
desktopX = (clientX - rect.left) * canvas.width  / rect.width
desktopY = (clientY - rect.top ) * canvas.height / rect.height
```

Read `rect`, `canvas.width/height` and `innerWidth/Height` live — `rect` changes
whenever the browser window resizes, and a stale rect is the usual cause of a
click that misses.

## The shared pointer

There is one X pointer and you share it with the user. `x0vncserver` injects
into the same pointer they're using, so:

- If they move the mouse during your action, your click lands somewhere else.
- Any calibration measured while they're active is garbage.

Ask them to keep hands off before you start clicking.

Recognise the signature of interference rather than chasing it: during
development, two calibration samples implied a *negative* y-scale — physically
impossible, and simply proof that the pointer had been moved between samples.
The coordinate model was correct the whole time. If your measurements
contradict each other, re-measure; don't "fix" the formula.

A useful discriminator when a click misbehaves — check whether the event reached
the page correctly before blaming the mapping:

```js
window.__last=null;
window.addEventListener('mousemove',e=>{window.__last={x:e.clientX,y:e.clientY};},true);
```

If `__last` matches `sent * s`, the browser side is fine and the discrepancy is
downstream — which in practice means the pointer was contested.

Verify effects out-of-band, always:

```bash
DISPLAY=:0 xdotool getmouselocation
DISPLAY=:0 xdotool getactivewindow getwindowname
```

## Safety

Clicks land on the user's real session, where actions are not sandboxed and not
always reversible. Confirm before anything irreversible — send, delete,
purchase, submit, confirm — the same standard as browser automation. Prefer
reading state to clicking through it when both are available.
