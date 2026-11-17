# Structured Output Schema

`rdt-cli` uses a shared agent-friendly envelope for machine-readable output.

## Success

```yaml
ok: true
schema_version: "1"
data: ...
```

## Error

```yaml
ok: false
schema_version: "1"
error:
  code: not_authenticated
  message: need login
```

## Notes

- `--json` and `--yaml` both use this envelope
- non-TTY stdout defaults to YAML
- reading and search commands return their payload under `data`
- `status` returns `data.authenticated` plus `data.cookie_count`
- `whoami` returns profile fields directly under `data`, including `data.name`
- common `error.code` values include `not_authenticated`, `rate_limited`, `not_found`, `forbidden`, and `api_error`
- set `OUTPUT=yaml|json|rich|auto` environment variable to override default format

## Pinned 0.4.2 payloads

- Listing/search with `--compact --json`: `data` is an array of posts with `id`, `title`, `selftext`, `permalink`, and other post fields.
- Listing/search without `--compact`: Reddit's Listing object is under `data`; posts are at `data.data.children[].data` and the continuation cursor is `data.data.after`. Pass the non-null cursor to the same command with `--after`, preserving filters. Compact output omits the cursor.
- `rdt read --json`: `data.post` and `data.comments[]`; each comment has `body`, `id`, `replies`, and additional fields. `more_count` and `more_children` indicate unexpanded content. Do not claim all comments were read unless coverage has been verified.
- `rdt export --format json`: a raw array of posts, without the success envelope. This is different from `search --json`.
- CSV: `title,subreddit,author,score,num_comments,url,permalink`, encoded as UTF-8 with a BOM. Use `utf-8-sig` for Python CSV readers.
- Permalinks in JSON can be relative; prefix `https://www.reddit.com` when presenting them as links.
