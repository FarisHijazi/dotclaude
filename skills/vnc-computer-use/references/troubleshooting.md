# Troubleshooting

Failure modes actually encountered while building and verifying this skill on
Ubuntu 25.04 + Chrome. Each entry says how to tell it apart from the others,
because several of them look identical from the outside (a blank screenshot).

## Triage: is it paint, handshake, or input?

These three break independently. Check in this order — it saves a lot of
guessing:

1. **Is the VNC server even talking?** A dead RFB handshake looks exactly like
   a dead paint.
   ```bash
   python3 - <<'EOF'
   import socket
   s = socket.create_connection(("127.0.0.1", 5901), timeout=5); s.settimeout(5)
   try: print("banner:", s.recv(32))
   except socket.timeout: print("TIMEOUT — server is not serving RFB")
   finally: s.close()
   EOF
   ```
   A healthy server replies `b'RFB 003.008\n'` immediately.

2. **Is the canvas receiving pixels?** Read the backing store directly — this
   works even when the tab is hidden and screenshots are blank:
   ```js
   const c=document.querySelector('canvas');
   const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
   let bright=0; for(let i=0;i<d.length;i+=4000) if(d[i]>40||d[i+1]>40||d[i+2]>40) bright++;
   JSON.stringify({w:c.width,h:c.height,bright,vis:document.visibilityState})
   ```
   `w`/`h` of 0 means not connected. `bright` well above 0 means pixels are
   arriving and your problem is purely the screenshot.

3. **Is input landing?** Ask the X server, not the picture:
   ```bash
   DISPLAY=:1 xdotool getmouselocation
   ```

## Screenshot is a blank dark rectangle

Most common by far. `document.visibilityState === "hidden"` — Chrome doesn't
composite background tabs, so the canvas never paints into the capture. The
canvas itself is fine (step 2 above proves it).

Use the mirror snippet from SKILL.md. Note that `resize_window` does **not**
make a tab visible, and neither does interacting with it; the tab has to
actually be foreground in its window, which you generally can't force.

Don't waste time on GPU/compositing flags — the mirror sidesteps the whole
issue.

## Screenshot times out after 30s

`CDP sendCommand "Page.captureScreenshot" timed out ... renderer may be frozen`.
Seen once on a backgrounded tab under a continuously-repainting canvas. It
succeeded on the immediate retry. Retry once before investigating; if it
repeats, refresh the mirror and screenshot again rather than reloading the page.

## Canvas stays 0×0 / title never changes

noVNC never completed the handshake. The page title is the tell: on success it
becomes the VNC desktop name (e.g. `claude - noVNC`), and stays plain `noVNC`
on failure.

Check `websockify`'s log for `connecting to: localhost:<port>` — if the TCP
connection is established but the title never updates, the VNC server is
accepting connections without serving RFB. Run the banner probe. Also note that
after the VNC server dies and restarts, the browser page must be **reloaded**;
`reconnect=1` does not always recover a socket that was proxied to a
now-dead server.

A `code 404, message File not found` line in the websockify log is just a
favicon request. Harmless.

## x11vnc starts, logs "screen setup finished", then never serves

Hit on Ubuntu 25.04. `x11vnc` reports `PORT=5900`, sits in state `R` burning
CPU, and never sends the RFB banner — the probe above times out.

Use TigerVNC's scraping server instead, which worked immediately on the same
display:

```bash
sudo apt-get install -y tigervnc-scraping-server
x0vncserver -display :0 -rfbport 5900 -localhost -SecurityTypes None -AlwaysShared
```

## Clicks land in the wrong place

On the **virtual desktop** with `resize=remote`, they shouldn't — canvas,
desktop, and viewport are all the same size and clicking what you see works.
If it's off, the desktop probably resized (the browser window changed size) and
your screenshot is stale: refresh the mirror and re-screenshot before clicking.

Confirm the geometry actually agrees:

```bash
DISPLAY=:1 xdpyinfo | grep dimensions
```
```js
JSON.stringify({vw:innerWidth,vh:innerHeight,c:document.querySelector('canvas').getBoundingClientRect().toJSON()})
```

On a **scaled or letterboxed** canvas (any real-display setup), raw coordinates
are not trustworthy — see `real-display.md`.

## `status` says "nothing running" but the port is open

`/usr/bin/x0vncserver` is a **Perl wrapper that re-execs**, so the `$!` captured
when you background it is already dead and any pidfile written from it is
useless. Resolve the process actually holding the port instead:

```bash
pgrep -f "x0vncserver -display :0 -rfbport 5900" | head -1
```

The bundled script does this. Same trap applies to any alternatives-managed
wrapper (`update-alternatives` installs `x0tigervncserver` behind this name).

## A cleanup command kills its own shell (exit 144)

`pkill -f 'x0vncserver -display'` matches **the invoking shell's own command
line**, because that string appears in it. The shell kills itself and you get
exit 144 with no useful output — easy to misread as the cleanup failing.

Use the script's `stop`, or match on something that can't appear in your own
command line, or kill by resolved PID.

## The window manager menu opens but the item doesn't run

It probably did run. Verify by process name rather than assumption:
`x-terminal-emulator` on this machine resolves to `terminator`, so
`pgrep xterm` reported nothing while the app had in fact launched. Check
`DISPLAY=:1 xwininfo -root -children` for new windows instead.
