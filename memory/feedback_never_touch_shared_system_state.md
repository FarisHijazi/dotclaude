---
name: Never touch shared system state to fix a problem
description: Hard rule — do not modify iptables, firewall rules, port bindings, reverse proxies, DNS, or other shared infra to work around a problem. Fix the root cause instead.
type: feedback
originSessionId: 8efa58f7-3e69-436d-b517-db3aa7354911
---
Never modify shared system state to work around a problem. This includes:
- `iptables` / `nftables` / `ufw` rules (NAT, redirects, forwarding)
- System firewall / port forwarding
- Reverse proxies (Traefik, nginx, caddy) configs
- Cloudflare tunnel ingress rules, DNS records
- `/etc/hosts`, `resolv.conf`, systemd-resolved
- Port bindings on privileged ports (80, 443, etc.)
- Anything that affects other apps/users on the machine

**Why:** These are shared resources. A redirect added to "fix" one app can silently hijack traffic for every other app/domain on the machine. The user caught me adding `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000` to work around a 502 from a Cloudflare tunnel — it routed every `*.fhijazi.me` domain through that tunnel to the wrong app. The real fix was `systemctl restart cloudflared` (stale QUIC connections), which I should have tried first.

**How to apply:**
- When something upstream (tunnel, proxy, DNS) is misrouting, investigate the upstream config, don't patch the origin to match bad routing.
- For 502/503 from a tunnel: restart the tunnel daemon, check its logs for stale connections, check that the origin is reachable on the configured port — don't change what port the origin listens on.
- If the only fix genuinely requires touching shared state: stop, explain to the user what I'd change and why, and wait for explicit approval.
- If I ever find myself running `iptables`, `ufw`, `systemctl stop <something-shared>`, or editing nginx/traefik configs "just to get this working," treat that as a red flag and back out.
