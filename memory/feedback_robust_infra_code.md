---
name: Infrastructure code must be portable and self-verifying
description: Never hardcode environment-specific values, always verify side effects, handle all edge cases in automation code
type: feedback
---

All infrastructure/automation code (Ansible, Terraform, shell scripts, Docker) must work on any target machine without modification.

**Why:** Repeated failures from assuming environment details that varied across hosts — hardcoded resource IDs that collided, package names that don't exist on newer distros, install scripts that failed silently, API parsers built on guessed field names. If it only works on the machine it was first developed against, it's not automation.

**How to apply:**

1. **Never hardcode local resource identifiers** (container IDs, VM IDs, IP addresses, paths). Always discover dynamically — query the system, use inventory variables, look up by name. External stable identifiers (Grafana.com dashboard IDs, package names, well-known ports) are fine to hardcode — they're constants, not environment-specific state.

2. **Verify every install/setup step.** After `curl | sh` or `apt install`, add a step that runs the binary with `--version` or checks it actually exists. "No error" ≠ "it worked."

3. **Don't assume package names or distro features.** What exists on Debian 12 may not exist on Debian 13. What works on Ubuntu may not work on Alpine. Check or use conditionals.

4. **Check real API responses before writing parsers.** Curl the endpoint, look at the actual JSON, then write the jq/parser. Don't guess field names from docs or memory.

5. **Default to idempotent operations.** Try to create → if exists, reuse. Never blindly delete-and-recreate. Every playbook/script should be safe to run twice.

6. **Handle all states:** DHCP vs static, service running vs stopped, resource exists vs missing, token fresh vs already created. Every branch must work.
