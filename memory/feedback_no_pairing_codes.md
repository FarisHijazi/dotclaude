# No pairing-code sign-in

The user strongly rejects pairing codes, including recurring code entry, copied
pairing links, and QR pairing offered as the normal sign-in solution. Do not keep
recommending pairing after this preference is stated.

For self-hosted applications, prefer the existing Authentik identity with normal
browser sign-in and automatic credential renewal across desktop, web, and mobile.
Preserve authentication and device security; eliminating manual codes is not
permission to disable authentication or create permanent shared credentials.

For T3 specifically, the user explicitly requested self-hosting the whole setup
and removing dependence on hosted T3 Connect/Clerk sign-in. Reuse existing service
owners and preserve running fleet sessions. Necessary authentication changes or
maintained patches are preferable to a pairing-code workaround. Implementation
and deployment details belong in the infrastructure repository's memory.
