---
name: Power-state restrictions
description: Generic recovery approval does not authorize machine shutdown, reboot, reset or power-cycle.
type: feedback
---

- Never initiate shutdown, reboot, reset or power-cycle through shell, APIs, KVM, GPIO or another interface.
- An exception requires the user to explicitly supersede this rule for the named power action and machine; generic recovery approval is insufficient.
- Do not automatically power a machine back on after requesting physical hardware work; its physical state may be unsafe.
