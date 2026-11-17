---
name: Unloaded and unavailable data
description: Keep loading, unavailable and genuinely empty states distinct in interfaces and APIs.
type: feedback
---

- Show a visible loading state until the first request settles. Use an explicit first-settle flag, not merely `!loading`.
- Keep that flag sticky during refreshes so existing content does not flash back to a skeleton.
- Disable controls while their underlying state is unknown; do not display unknown booleans as false or unknown counts as zero.
- Distinguish unavailable/error responses from successful empty results in both APIs and UI, with an explicit availability state and reason.
- Settle the loading state on errors and when no request will be made, such as a disabled feature or missing access.
- Verify that the loading indicator actually renders visibly.
