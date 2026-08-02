#!/usr/bin/env bash
# VNC + noVNC bridge so Claude can drive a desktop through claude-in-chrome.
#
#   real     mirror the user's live session (:0) — their signed-in apps and
#            open windows. This is what you almost always want.
#   virtual  a private headless desktop (:1) — scratch work only. Apps started
#            here are fresh: no cookies, no logins, none of the user's windows.
set -euo pipefail

MODE="${2:-real}"
RUNDIR=/tmp/claude-vnc
mkdir -p "$RUNDIR"

REAL_DISPLAY="${VNC_REAL_DISPLAY:-:0}"
REAL_RFB="${VNC_REAL_RFB:-5900}"
REAL_WEB="${VNC_REAL_WEB:-6081}"

VIRT_NUM="${VNC_DISPLAY:-1}"
VIRT_RFB=$((5900 + VIRT_NUM))
VIRT_WEB="${VNC_WEB_PORT:-6080}"
GEOMETRY="${VNC_GEOMETRY:-1280x800}"
WM="${VNC_WM:-openbox}"

pidfile() { echo "$RUNDIR/$1.pid"; }
alive()   { local f; f=$(pidfile "$1"); [[ -f $f ]] && kill -0 "$(cat "$f")" 2>/dev/null; }
stop_one(){ local f; f=$(pidfile "$1"); [[ -f $f ]] || return 0
            kill "$(cat "$f")" 2>/dev/null || true; rm -f "$f"; }

# A server that accepts TCP but never sends the RFB banner is a real failure
# mode (x11vnc does this on Ubuntu 25.04) and looks identical to a rendering
# problem in the browser. Check it here instead of guessing later.
probe_rfb() {
  python3 - "$1" <<'EOF'
import socket, sys
try:
    s = socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=5)
    s.settimeout(5)
    print("rfb ok:", s.recv(12).decode(errors="replace").strip())
except Exception as e:
    print("rfb FAILED:", e); sys.exit(1)
EOF
}

start_real() {
  if alive x0vnc; then echo "already running"; status; return 0; fi
  command -v x0vncserver >/dev/null || {
    echo "need: sudo apt-get install -y tigervnc-scraping-server novnc websockify" >&2; exit 1; }

  x0vncserver -display "$REAL_DISPLAY" -rfbport "$REAL_RFB" -localhost \
    -SecurityTypes None -AlwaysShared >"$RUNDIR/x0vnc.log" 2>&1 &
  sleep 3
  # /usr/bin/x0vncserver is a perl wrapper that re-execs, so $! is already dead.
  # Resolve the process actually holding the port.
  pgrep -f "x0vncserver -display ${REAL_DISPLAY} -rfbport ${REAL_RFB}" | head -1 >"$(pidfile x0vnc)"
  probe_rfb "$REAL_RFB" || { echo "see $RUNDIR/x0vnc.log" >&2; exit 1; }

  websockify --web=/usr/share/novnc "127.0.0.1:${REAL_WEB}" "localhost:${REAL_RFB}" \
    >"$RUNDIR/ws-real.log" 2>&1 &
  echo $! >"$(pidfile ws-real)"
  sleep 1
  status
}

start_virtual() {
  if alive xvnc; then echo "already running"; status; return 0; fi
  rm -f "/tmp/.X${VIRT_NUM}-lock" "/tmp/.X11-unix/X${VIRT_NUM}" 2>/dev/null || true

  Xtigervnc ":${VIRT_NUM}" -geometry "$GEOMETRY" -depth 24 \
    -SecurityTypes None -localhost -rfbport "$VIRT_RFB" \
    -AlwaysShared -desktop claude >"$RUNDIR/xvnc.log" 2>&1 &
  echo $! >"$(pidfile xvnc)"

  for _ in $(seq 40); do
    DISPLAY=":${VIRT_NUM}" xdpyinfo >/dev/null 2>&1 && break; sleep 0.25
  done
  DISPLAY=":${VIRT_NUM}" xdpyinfo >/dev/null 2>&1 || {
    echo "Xtigervnc failed:"; cat "$RUNDIR/xvnc.log"; exit 1; }

  DISPLAY=":${VIRT_NUM}" "$WM" >"$RUNDIR/wm.log" 2>&1 &
  echo $! >"$(pidfile wm)"

  websockify --web=/usr/share/novnc "127.0.0.1:${VIRT_WEB}" "localhost:${VIRT_RFB}" \
    >"$RUNDIR/ws-virt.log" 2>&1 &
  echo $! >"$(pidfile websockify)"
  sleep 1
  status
}

status() {
  for s in x0vnc ws-real xvnc wm websockify; do
    alive "$s" && printf '%-11s up (pid %s)\n' "$s" "$(cat "$(pidfile "$s")")"
  done
  if alive x0vnc; then
    echo "REAL  ${REAL_DISPLAY} $(DISPLAY=$REAL_DISPLAY xdpyinfo 2>/dev/null | awk '/dimensions/{print $2}')"
    echo "URL   http://localhost:${REAL_WEB}/vnc.html?autoconnect=1&resize=scale&reconnect=1"
  fi
  if alive xvnc; then
    echo "VIRT  :${VIRT_NUM} $(DISPLAY=:${VIRT_NUM} xdpyinfo 2>/dev/null | awk '/dimensions/{print $2}')"
    echo "URL   http://localhost:${VIRT_WEB}/vnc.html?autoconnect=1&resize=remote&reconnect=1"
  fi
  alive x0vnc || alive xvnc || echo "nothing running"
}

case "${1:-start}" in
  start)   case "$MODE" in
             real)    start_real ;;
             virtual) start_virtual ;;
             *) echo "mode must be real|virtual" >&2; exit 1 ;;
           esac ;;
  stop)    for s in ws-real x0vnc websockify wm xvnc; do stop_one "$s"; done; echo "stopped" ;;
  restart) "$0" stop; sleep 1; "$0" start "$MODE" ;;
  status)  status ;;
  *) echo "usage: $0 {start|stop|restart|status} [real|virtual]"; exit 1 ;;
esac
