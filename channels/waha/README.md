# WAHA WhatsApp Channel for Claude Code

Two-way WhatsApp chat bridge via WAHA (WhatsApp HTTP API).

## Setup

1. Add to your MCP config (user-level `~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "waha": {
      "command": "bun",
      "args": ["/Users/farishijazi/.claude/channels/waha/waha-channel.ts"],
      "env": {
        "WAHA_API_URL": "https://waha.fhijazi.com",
        "WAHA_API_KEY": "sk-bekfast",
        "WAHA_SESSION": "default",
        "WAHA_ALLOWED_CHATS": "",
        "WAHA_WEBHOOK_PORT": "8789"
      }
    }
  }
}
```

2. Configure WAHA to send webhooks to `http://localhost:8789` (or use an SSH tunnel / ngrok if WAHA is remote).

3. Launch Claude Code with the channel:

```bash
claude --dangerously-load-development-channels server:waha
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WAHA_API_URL` | `https://waha.fhijazi.com` | WAHA API base URL |
| `WAHA_API_KEY` | (empty) | WAHA API key (`X-Api-Key` header) |
| `WAHA_SESSION` | `default` | WAHA session name |
| `WAHA_ALLOWED_CHATS` | (empty) | Comma-separated chat IDs to accept (empty = accept all) |
| `WAHA_WEBHOOK_PORT` | `8789` | Local port for WAHA webhook receiver |

## Webhook Configuration

WAHA needs to POST message events to this channel's local HTTP server. For a remote WAHA server, you need a tunnel:

```bash
# Option 1: SSH reverse tunnel
ssh -R 8789:localhost:8789 your-waha-server

# Option 2: ngrok
ngrok http 8789
```

Then configure WAHA session webhooks:

```bash
curl -X PUT "https://waha.fhijazi.com/api/sessions/default" \
  -H "X-Api-Key: sk-bekfast" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "webhooks": [{
        "url": "http://localhost:8789",
        "events": ["message"]
      }]
    }
  }'
```

## Tools Provided

- **waha_reply** — Send a WhatsApp text message (with optional reply-to)
- **waha_send_seen** — Mark a chat as read

## Features

- Two-way: receive WhatsApp messages, Claude replies via `waha_reply` tool
- Sender gating via `WAHA_ALLOWED_CHATS`
- Permission relay: forwards Claude's tool approval prompts to first allowed chat
- Media detection: flags messages with media attachments
