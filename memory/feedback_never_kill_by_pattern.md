---
name: Never kill processes by a broad pattern
description: pkill/killall/pgrep -f match the WHOLE command line — verify matches by reading them, then kill by PID. Applies to any destructive pattern (xargs rm, find -delete, sed -i).
type: feedback
---

A pattern that selects what to DESTROY must be verified by reading its matches first.

**Why:** `pkill -f 5000`, run on a Proxmox host to clean up my own port-50004/50005 probes, killed a
running VM — every QEMU process carries `reconnect-ms=5000` in its `qmp-event` socket argument. The
journal recorded `kvm: terminating on signal 15`, the VM hard-stopped with a backup in flight (that
backup failed and was lost), and every service on it went down. Nothing warned me; `pkill` prints
nothing and exits 0.

**How to apply:**
1. **Look before you kill.** `pgrep -af <pattern>` (or `ps aux | grep`) and READ the full command
   lines. If even one line is not mine, the pattern is wrong — narrow it, don't proceed.
2. **Kill the exact PID**, not the pattern. Capture it at launch (`$!`, or a pidfile) and
   `kill "$PID"`. A pattern is a guess; a PID is not.
3. **Anchor** an unavoidable pattern to a full path or unique token
   (`pkill -f '^/usr/bin/myworker --id=abc123'`) — never a bare number, port, or common word.
4. **Never kill processes on a hypervisor, router, NAS or other shared/host machine** — the blast
   radius is other people's VMs, not my task. Use the platform's own verb (`qm stop`, `docker stop`,
   `systemctl stop`) instead of signalling processes. See [[feedback_never_touch_shared_system_state]].
5. Same care for destructive greps-turned-actions: `xargs rm`, `find -delete`,
   `grep -l … | xargs sed -i`. Print the match list, read it, then act on that list.

Cleanup code deserves more care than the thing it cleans up, not less.
