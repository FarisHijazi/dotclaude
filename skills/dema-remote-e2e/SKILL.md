# e2e tests

for end to end testing, this requires the entire docker compose stack and dev stack and services to be running.

IMPORTANT: unit tests are not enough!!! end to end testeing and virtual device deployment and testing and probing must be done as this is a complex and safety-critical system!

## setup

The current fm3 macbook is not strong enough to run these tests, so you can use either of these 2 machines:
- ssh faris@buzastation:~/Projects/dema/control-service (not always online)
- ssh faris@dema-dev:~/Projects/demaenergy.d/control-service
- ssh fh@dema-ahmed-dev:~/Projects/dema/control-service
(never use dema-dev-1 for testing)

it's very important that when testing, you checkout the correct branches (usually master) for all the repos, you can checkout the features being tested but usually most repos should be on master if they're not being tested. The e2e tests will use the folders in the root (i.e .../demaenergy.d/, .../dema/ etc) not git worktrees, so it's important that the folders have up to date clean worktrees.
Use `bash pull_all_repos.sh` to pull the latest code from all the repos. If that script is not present on the host (e.g. buzastation has none), a self-contained copy ships with this skill (`pull_all_repos.sh` in the skill dir) — copy it over and run it (`bash pull_all_repos.sh` for a non-destructive ff-only pull of each repo's current branch, or `bash pull_all_repos.sh --master` to switch every clean repo to master first). It prints a repo/branch/sha/state table so you can confirm every repo not under test is on `master` and up-to-date.

### ⚠️ ALWAYS pull EVERY repo to master BEFORE any ETP / `grid_etp_test.py` run

This is the #1 recurring foot-gun on the e2e hosts — a stale checkout on ONE repo
silently breaks the whole ETP suite in a way that looks like a code regression but
is not. It bit **3× in a single session (2026-07-19)**. The ETP path is uniquely
fragile because of **cross-repo register lockstep**: modbus-server (`register_map.yaml`
offsets) ↔ virtual-etp (`_INPUT_BLOCK_LEN`, holding offsets) ↔ grid-gateway
(`get_state_dict` fields like `plc_init_phase`). If any one lags master:

- **modbus-server stale** (fewer input registers than virtual-etp reads) → virtual-etp
  container goes `unhealthy`, logs loop `modbus loop error: short input read: 0/43;
  reconnecting`, writes no holding registers → **every** `grid_etp` test fails with
  `virtual-etp did not confirm switch to local mode` and `grid_frequency_hz=0.0`.
- **grid-gateway stale** (missing a newer `get_state_dict` field, e.g. `plc_init`) →
  that field reads `None`, so the guard/test that keys on it fails (`plc_init_phase=None`)
  even though the production code is fine.

**Do NOT debug the test code or suspect a regression until every repo is confirmed at
origin/master.** Diagnose a suspected lockstep break with:

```bash
docker logs dfc-virtual-etp-1 2>&1 | grep -i 'short input read' | tail   # stale-modbus symptom
# compare virtual-etp _INPUT_BLOCK_LEN vs the max input offset in modbus-server register_map.yaml
git -C <repo> log --oneline -1; git -C <repo> status -sb   # is each repo actually at origin/master?
```

See memory `project_etp_modbus_register_lockstep` and `project_etp_plc_reboot_quirk`.

it's also important to make sure that no e2e tests are already running, if there are, choose another machine or wait for them to finish.

NOTE: make sure you run the tests in tmux and check on them in case they disconnect, because they can take over 10 minutes to run. Be sure to cleanup the tmux session when you're completely done with all the testing and probing and the user is done. Also you can find out if there are already e2e tests or probes running by checking the tmux sessions

## Disk hygiene

Repeated e2e runs fill the disk and can take the host down. Before starting, if
`df -h /` is tight, run `bash cleanup_disk.sh` on the e2e host to reclaim space.

## Manners

in the root of the project write a busy.lock.yaml with the following fields:

```yaml
# busy.lock.yaml
started_at: "2026-06-23 10:00:00"
ttl_minutes: 45 # if this time passes then the lock is considered expired and other users/claude sessions can start a new test, if you are running the tests and are noticing it's taking a long time, then you can update the ttl_minutes to extend the time.
claude_session_id: "..."
source_machine: "fm3" # the machine you're running the tests from
tmux_session_name: "..."
repos_branches: # all repos would be on master unless otherwise specified in this list (note that this does nothing, it's just for documentation purposes)
    - "control-service:feat/scheduler-demaops-poller"
    - "dema-ops-backend:feat/schedule-service-token"
feature_description: "control-service polls dema-ops-backend for schedules and uses API tokens"
```

this file describes if a test is being run, to find which machine is free, you can check this file and see if it has expired or not or if it doesn't exist then you can use this machine. if all machines are full you can poll but note that the file might get updated in real time so be sure to read it before starting the tests.
when you're done with running your tests, you can move the file to `busy-YYMMDDHHMMSS.yaml` as a way to log what tests ran.

## testing

- run automatic e2e tests
- **Flaky safety-property tests: investigate, never loosen blindly.** Some e2e tests
  assert a *safety* invariant (e.g. `test_global_estop_freezes_and_recovers` — that a
  freeze actually holds power). If one flakes intermittently, do NOT widen/loosen its
  assertion to make it green — that discards the exact signal it exists to catch.
  Reproduce and understand the flake first; flag it for a separate look rather than
  papering over it. (Distinct from a genuinely mis-designed test-timing flake, which is
  fine to fix in test code — the difference is whether the assertion encodes a real
  system guarantee.)
- after the e2e tests, now that the services are running, you can probe and interact and run manual tests to verify certain behaviors or features. heavily test edge cases, run adversarial tests, test all the edge cases and behaviors and make sure the feature is robust.
- you should even use /chrome for testing anything that has a frontend, connect to the host (buzastation, dema-dev, dema-ahmed-dev, ...) on the browser, don't be shy! EVERYTHING MUST BE TESTED!

