---
name: Shared-system boundaries
description: Fix an application's root cause without collateral changes to shared infrastructure.
type: feedback
---

- Do not change shared routing, firewall rules, DNS, reverse proxies or port bindings as a workaround for an application problem.
- Inspect the owning configuration and logs to identify the actual fault; do not prescribe a blanket service restart.
- A necessary shared-state change requires explicit authorization for that change and its affected services, with the impact explained beforehand.
