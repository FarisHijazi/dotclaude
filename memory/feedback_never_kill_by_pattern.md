---
name: Process and cleanup safety
description: Verify exact targets and preserve shared or user-owned state during cleanup.
type: feedback
---

- Read the matching processes before acting, then use an exact verified PID or the PID saved at launch. Never kill by pattern.
- On hypervisors, routers, NAS or other shared hosts, use the owning platform's authorized actions instead of raw process signals. Power-state restrictions still apply.
- For test cleanup, remove only the exact processes, sessions and files created by that test. Inspect and verify the explicit target list before any destructive batch action.
