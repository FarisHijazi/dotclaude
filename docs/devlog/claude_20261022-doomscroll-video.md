# explainer-video → doomscroll-video

The public skill is now the Doomscroll thin client, a copy of `agent-plugin/skills/doomscroll-video/` in the Doomscroll
repo (edit there, then copy SKILL.md and scripts/doomscroll.mjs here). The user's agent investigates the change and
the system around it, writes notes (components with kinds, architecture, flows, risks), picks the language and skin,
and Doomscroll renders in the cloud. Real video work still uses the private `video-studio` plugin.

Verified 2026-10-22: a local change with notes rendered on doomscroll.build in about 3 minutes; the storyboard used
components and risks that were only in the notes.
