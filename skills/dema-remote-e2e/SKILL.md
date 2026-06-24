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
Use `bash pull_all_repos.sh` to pull the latest code from all the repos.

it's also important to make sure that no e2e tests are already running, if there are, choose another machine or wait for them to finish.

NOTE: make sure you run the tests in tmux and check on them in case they disconnect, because they can take over 10 minutes to run. Be sure to cleanup the tmux session when you're completely done with all the testing and probing and the user is done. Also you can find out if there are already e2e tests or probes running by checking the tmux sessions

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
- after the e2e tests, now that the services are running, you can probe and interact and run manual tests to verify certain behaviors or features. heavily test edge cases, run adversarial tests, test all the edge cases and behaviors and make sure the feature is robust.

