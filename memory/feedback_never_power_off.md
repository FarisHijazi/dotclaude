---
name: Never shut down machines
description: Never shut down, reboot, or power-cycle a machine; generic recovery approval is not permission.
type: feedback
---

User explicitly reiterated on 2026-11-09: never shut down a machine again. Never initiate shutdown, reboot, reset, or power-cycle through shell, platform API, KVM, GPIO, or any other interface. Do not infer an exception from “recover”, “continue”, “approved”, or “go ahead”. Keep recovery online. A future exception requires the user to explicitly supersede this prohibition for the named power action and machine.

This follows an incorrect shutdown of pve3 after interpreting generic recovery approval as readiness for a powered-off cable check. Do not automatically power it back on after requesting physical hardware work; its physical state may be unsafe.
