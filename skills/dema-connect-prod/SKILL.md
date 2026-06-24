feel free to read the production db but make sure to always filter by time, also never write to the production db, just investigate etc, feel free to connect to the production services (ssh dema-control-service, dema-telemetry, ...)


## Safety

- NEVER do anything destructive to the production environment, in the rare case where something destructive is needed, ask for explicit permission first.
- NEVER modify the production DB without double confirming for explicit permission first.
- shutdown hosts or stop services without asking for permission

## Hosts

```sh
Host dema-grid-gateway
  HostName 10.100.20.19
  User service

Host dema-discovery
  HostName 10.100.20.8
  User service

Host dema-telemetry
  HostName 10.100.20.21
  User service

Host dema-ray-head
  HostName 10.100.20.18
  User service

Host dema-control-service
  HostName 10.100.20.20
  User service

Host dema-dema-ops
  HostName 10.100.20.22
  User service

# only tinker tools scripts are used here no other reason to ssh here except for arp-scan and tinker-tools scripts
Host dema-dev-1
  HostName 10.100.20.77
  User service

# really try to avoid using this one unless strictly necessary and ask for explicit permission
Host dema-proxmox
  HostName 10.100.1.49
  User root
```

## Deploy / env vars (CI/CD runners) — do NOT edit host `.env`

Prod env lives in each repo's GitHub **Environment `production-ibri-1`**, in the `ENV_FILE`
**variable** (not a secret). The CI/CD workflow (self-hosted runner) renders `ENV_FILE` → the
host `.env`, pulls from ghcr, and recreates the container. So:

- **Never edit the host `/home/service/<repo>/.env`** — it's overwritten next deploy. Change the
  `ENV_FILE` variable instead. (Also: the hosts have no ghcr login, so a manual `docker compose up`
  fails with `denied` / `No such image` — only the runner can deploy.)
- Read: `gh api repos/DEMAEnergy/<repo>/environments/production-ibri-1/variables/ENV_FILE --jq .value`
- Write: `gh variable set ENV_FILE --env production-ibri-1 --repo DEMAEnergy/<repo> < file`
  (stdin; there is no `--body-file`).
- Apply: `gh run rerun <last CI/CD run id> --repo DEMAEnergy/<repo>` (vars are read at run time).

## Mistakes I made (don't repeat)
- Edited the host `.env` directly to enable the poller — wrong; reverted. Use `ENV_FILE` + rerun.
- Tried `docker compose up` on the host to apply env — fails (no ghcr login).

## Prod DemaOps (`ssh dema-dema-ops`, 10.100.20.22)
- Backend `demaops-demaops-backend-1` → `http://10.100.20.22:8000`; DB is **external**
  (`10.100.20.16/demaops`, no local db container, no `psql` on host).
- Query/seed/mint-keys by running the app's repos inside the backend container:
  `docker cp x.py demaops-demaops-backend-1:/tmp/ && docker exec -w /app demaops-demaops-backend-1 uv run --no-sync python /tmp/x.py`.
- Controller reaches DemaOps at `http://10.100.20.22:8000` — NOT the dev name `demaops-backend:8000`.
- Prod controller has `ENABLE_POWER_SETPOINT=true`: enabling the schedule poller makes it act on
  the live schedule. Safe only when the schedule is transparent or miners have setpoints disabled.
