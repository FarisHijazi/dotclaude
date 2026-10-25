# Linux `/sudo` passkeys and native login clicks

## Problem

On Linux, `skills/sudo/scripts/confirm-passkey.sh` always called macOS Hammerspoon at
`/opt/homebrew/bin/hs`, so Bitwarden passkey confirmation failed immediately. Running
Chrome did not expose its extension popup through AT-SPI, even after installing
`python3-pyatspi` and enabling Chrome accessibility.

## Change

- `confirm-passkey.sh` keeps fresh approval, then dispatches Linux to
  `press_passkey_linux.py`.
- The Linux helper finds Bitwarden's exact Chrome extension popup:
  `WM_CLASS=crx_nngceckbapebfimnlniiiahkandclblb, Google-chrome`, title `Bitwarden`, role
  `pop-up`. It screenshots only that window, reads Tesseract TSV, requires the
  authentication heading and one high-confidence exact domain, rechecks focus and geometry,
  then sends one native XTEST click.
- `sudo.sh --via google|passkey --title <prefix> --window-id <XID> --click X,Y` performs one
  native Chrome click after approval. The caller must screenshot-verify the destination and
  coordinates. It never autofills or presses Return.
- Linux dependencies on `dev`: `xdotool`, `xprop`, `scrot`, `tesseract-ocr`.

## Verification (2026-10-25, `dev` Linux Chrome)

- Regressions: `python3 ~/.claude/skills/sudo/tests/passkey_linux_test.py -v`, 19 tests OK.
- GitHub sudo mode: `confirm-passkey.sh github.com` printed `pressed`. GitHub changed from
  Confirm access to GitHub App settings.
- Google: `sudo.sh ... --via google --window-id ... --click ...` printed `clicked` and advanced
  from email entry to passkey challenge. `confirm-passkey.sh accounts.google.com` printed
  `pressed` and loaded the signed-in Google Account page.
- An expired passkey challenge, or calling before the popup has rendered, fails closed with exit 2.
  Retry for a few seconds after the click that opens it (exit 2 sends nothing).
- Independent review found one gap: the list could re-render between the OCR and the click.
  The helper now reads the popup twice and refuses when the matched row moved (covered in
  `test_passkey_failure_sends_no_click`). The full Google flow was re-run after that change and
  reached the signed-in Google Account page.

## Follow-up: built-in waiting and evidence screenshots

- `confirm-passkey.sh` now waits for the popup itself (`--wait`, default 20 s), so callers run it
  right after clicking the page's passkey button. After the click it waits for Bitwarden to close the
  popup; still open after 10 s = exit 5.
- `--click` screenshots the window before (after the pointer moved) and after the click; no visible
  change within 10 s = exit 5.
- Both print a `$TMPDIR/sudo/evidence/<kind>-<time>/` folder (mode 0700) with `popup.png` or
  `before.png`, plus `after.png`, for the caller to read.
- 22 desktop-free tests (fake clock; late popup, popup left open, click with no change).
- Live on `dev`: one `sudo.sh --click` on Google's Next (`window changed`), then
  `confirm-passkey.sh accounts.google.com` run immediately with no external retry
  (`popup closed`), ending on myaccount.google.com. The screenshots showed the Google loading state
  and "Verifying it's you".

## Follow-up: parent relying party (second Linux VM)

On a second Linux VM the Google passkey is a Bitwarden item with a custom name; its card shows the relying
party `google.com`, not `accounts.google.com`, so the exact match failed closed (exit 2). The helper
now tries the exact domain, then each parent that still has a dot (WebAuthn allows a registrable
parent as rpId), and still requires exactly one match at that level. 24 tests.
