---
name: dema-feat
description: instructions for setting up and developing and testing a new feature for dema/DFC/control-service, usually in ~/Projects/demaenergy.d/ or ~/Projects/dema/
---

You must implement the the user's requested feature

1. make sure to git pull and start from a fresh clean updated master branch
2. then create a new git worktree and work there (worktree should be in /<original repo path>/worktrees/<your new worktree>/)
3. planning and development
4. be sure to test this comprehensively and run /dema-remote-e2e (read @/Users/farishijazi/.claude/skills/dema-remote-e2e/SKILL.md), even use /chrome for testing if needed
5. Create a PR and review the PR comments
6. don't forget to wait a few minutes until the PR review bot posts it's findings, then address any valid PR comments and commit and push to the PR. then wait again for the PR review claude code bot. Repeat step 6 until there's no longer any more valid comments (you don't need to listen to PR comments that are invalid)
7. IFF I ask for deploying the feature to production, then I need you to actually test that it succeeded in production deployment and the runner succeeded etc and if you need to debug, then if you must, use /dema-connect-prod (read @/Users/farishijazi/.claude/skills/dema-connect-prod/SKILL.md), and for anything that has a frontend, use /chrome to actually test the deployment not just with curl commands!

ultrathink and make no mistakes

don't worry about context size getting close to 100%, it will auto-compact on it's own, just keep going and don't stop until the feature itself is fully done and tested
