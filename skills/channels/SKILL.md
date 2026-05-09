---
name: channels
description: |
  Build Claude Code channel servers (MCP servers that push external events into a running session).
  Scaffolds one-way (alerts/webhooks) or two-way (chat bridge) channels with sender gating,
  reply tools, and optional permission relay. Knows the full MCP channel protocol.
  Use for ANY channel building, WhatsApp/WAHA, Telegram, Discord, webhook receivers, CI alerts, etc.
triggers:
  - channel
  - /channel
  - channels
  - build channel
  - create channel
  - whatsapp channel
  - waha channel
  - telegram channel
  - discord channel
  - webhook channel
  - ci channel
  - alert channel
  - chat bridge
  - push events
  - push notifications channel
  - mcp channel
invocable: true
argument-hint: "[platform] [one-way|two-way]"
---

# /channels - Build Claude Code Channel Servers

Build MCP servers that push external events into a running Claude Code session. Channels are the bridge between external systems (WhatsApp, Telegram, CI, monitoring, webhooks) and Claude.

## Agent Invariants

**MUST follow these rules:**

1. **Always use Bun** as the runtime (built-in HTTP server, TypeScript, fastest startup)
2. **Always use `@modelcontextprotocol/sdk`** — the only hard dependency
3. **Gate inbound messages** — ungated channels are prompt injection vectors
4. **Listen on 127.0.0.1 only** — never expose to the network
5. **Use stdio transport** — Claude Code spawns channels as subprocesses
6. **Load env from `~/.env`** or `~/.claude/channels/<name>/.env` — never hardcode secrets
7. **Include instructions** in the Server constructor — Claude needs to know how to handle events

## Channel Architecture

```
External system (WhatsApp, CI, webhook, chat platform)
  -> Your channel server (local process, spawned by Claude Code)
  -> MCP notification over stdio
  -> Arrives in Claude's context as <channel source="name" ...>
  -> Claude reads and acts (one-way) or replies via tool (two-way)
```

## Protocol Reference

### Capability Declaration

```typescript
const mcp = new Server(
  { name: 'your-channel', version: '0.0.1' },
  {
    capabilities: {
      experimental: {
        'claude/channel': {},                    // REQUIRED: registers notification listener
        'claude/channel/permission': {},         // OPTIONAL: permission relay
      },
      tools: {},                                 // OPTIONAL: two-way only, for reply tool
    },
    instructions: 'Events arrive as <channel source="your-channel" ...>. ...',
  },
)
```

### Notification Format

```typescript
await mcp.notification({
  method: 'notifications/claude/channel',
  params: {
    content: 'the event body',                   // becomes <channel> tag body
    meta: { key: 'value' },                      // each key becomes a tag attribute
  },
})
```

- `content`: string — the event body, delivered as `<channel>` tag body
- `meta`: Record<string, string> — optional, each entry becomes a tag attribute
  - Keys must be identifiers: letters, digits, underscores only
  - Keys with hyphens or special chars are silently dropped

### Reply Tool (Two-Way)

```typescript
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'reply',
    description: 'Send a message back over this channel',
    inputSchema: {
      type: 'object',
      properties: {
        chat_id: { type: 'string', description: 'The conversation to reply in' },
        text: { type: 'string', description: 'The message to send' },
      },
      required: ['chat_id', 'text'],
    },
  }],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  if (req.params.name === 'reply') {
    const { chat_id, text } = req.params.arguments as { chat_id: string; text: string }
    // POST to your platform API here
    return { content: [{ type: 'text', text: 'sent' }] }
  }
  throw new Error(`unknown tool: ${req.params.name}`)
})
```

### Permission Relay (Optional)

Declare `'claude/channel/permission': {}` in capabilities, then:

```typescript
import { z } from 'zod'

const PermissionRequestSchema = z.object({
  method: z.literal('notifications/claude/channel/permission_request'),
  params: z.object({
    request_id: z.string(),     // 5 lowercase letters (no 'l')
    tool_name: z.string(),
    description: z.string(),
    input_preview: z.string(),
  }),
})

mcp.setNotificationHandler(PermissionRequestSchema, async ({ params }) => {
  // Forward to chat platform with the request_id
  sendToUser(`Claude wants to run ${params.tool_name}: ${params.description}\nReply "yes ${params.request_id}" or "no ${params.request_id}"`)
})

// In inbound handler, intercept verdict replies:
const PERMISSION_REPLY_RE = /^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$/i
const m = PERMISSION_REPLY_RE.exec(text)
if (m) {
  await mcp.notification({
    method: 'notifications/claude/channel/permission',
    params: {
      request_id: m[2].toLowerCase(),
      behavior: m[1].toLowerCase().startsWith('y') ? 'allow' : 'deny',
    },
  })
  return // don't forward as chat
}
```

### Sender Gating

```typescript
const allowed = new Set(loadAllowlist())
if (!allowed.has(message.from.id)) return  // gate on SENDER, not room/chat
```

## Scaffold Templates

### One-Way (Webhook Receiver)

```typescript
#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'

const mcp = new Server(
  { name: 'webhook', version: '0.0.1' },
  {
    capabilities: { experimental: { 'claude/channel': {} } },
    instructions: 'Events from webhook arrive as <channel source="webhook">. Read and act.',
  },
)
await mcp.connect(new StdioServerTransport())

Bun.serve({
  port: 8788,
  hostname: '127.0.0.1',
  async fetch(req) {
    const body = await req.text()
    await mcp.notification({
      method: 'notifications/claude/channel',
      params: { content: body, meta: { path: new URL(req.url).pathname } },
    })
    return new Response('ok')
  },
})
```

### Two-Way (Chat Bridge)

```typescript
#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'

const mcp = new Server(
  { name: 'chat-bridge', version: '0.0.1' },
  {
    capabilities: {
      experimental: { 'claude/channel': {} },
      tools: {},
    },
    instructions: 'Messages arrive as <channel source="chat-bridge" chat_id="..." sender="...">. Reply with the reply tool, passing chat_id.',
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'reply',
    description: 'Send a reply back through this channel',
    inputSchema: {
      type: 'object',
      properties: {
        chat_id: { type: 'string' },
        text: { type: 'string' },
      },
      required: ['chat_id', 'text'],
    },
  }],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  if (req.params.name === 'reply') {
    const { chat_id, text } = req.params.arguments as { chat_id: string; text: string }
    await platformSendMessage(chat_id, text)  // implement per platform
    return { content: [{ type: 'text', text: 'sent' }] }
  }
  throw new Error(`unknown tool: ${req.params.name}`)
})

await mcp.connect(new StdioServerTransport())
// Start platform-specific listener (polling, websocket, HTTP webhook, etc.)
```

## Registration

### .mcp.json (project-level)

```json
{
  "mcpServers": {
    "your-channel": { "command": "bun", "args": ["./your-channel.ts"] }
  }
}
```

### ~/.claude.json (user-level, use absolute paths)

```json
{
  "mcpServers": {
    "your-channel": { "command": "bun", "args": ["/absolute/path/to/your-channel.ts"] }
  }
}
```

## Running

```bash
# During research preview (custom channels not on allowlist)
claude --dangerously-load-development-channels server:your-channel

# Official plugins
claude --channels plugin:telegram@claude-plugins-official

# Multiple channels
claude --channels plugin:telegram@claude-plugins-official --dangerously-load-development-channels server:webhook
```

## Platform-Specific Notes

### WAHA (WhatsApp)

- API base: configurable (e.g. https://waha.example.com)
- Auth: `X-Api-Key` header
- Webhook events: `message`, `message.any`, `message.reaction`, `message.ack`
- Send text: `POST /api/sendText` with `{ session, chatId, text }`
- ChatId format: `12345@c.us` (user), `12345@g.us` (group)
- Media: `hasMedia: true` with `media.url` for download
- Webhook payload: `{ event, session, payload: { id, timestamp, from, to, body, hasMedia } }`
- Configure webhooks: `POST /api/sessions/` with `config.webhooks[].url` and `.events`
- Reply to message: add `reply_to: "messageId"` to send payload
- Env vars: `WAHA_API_URL`, `WAHA_API_KEY`, `WAHA_SESSION` (default: "default")

### Telegram

- Use BotFather to create bot, get token
- Plugin: `plugin:telegram@claude-plugins-official`
- Polls Telegram API (no webhook URL needed)

### Discord

- Create bot in Developer Portal, enable Message Content Intent
- Plugin: `plugin:discord@claude-plugins-official`
- Connects via Discord gateway (no webhook URL needed)

### Generic Webhook

- Any system that can HTTP POST (CI, monitoring, cron)
- Listen on local port, forward body as channel event
- No auth needed if localhost-only; add `X-Sender` header for gating

## Decision Tree

```
Building a channel?
+-- What platform?
|   +-- WhatsApp (WAHA)? -> Two-way chat bridge, poll /api/messages or receive webhooks
|   +-- Telegram?        -> Use official plugin or build custom with Bot API polling
|   +-- Discord?         -> Use official plugin or build custom with gateway
|   +-- CI/Monitoring?   -> One-way webhook receiver
|   +-- Custom HTTP?     -> One-way or two-way depending on needs
|
+-- One-way or two-way?
|   +-- One-way (alerts) -> No tools capability, no reply handler
|   +-- Two-way (chat)   -> Add tools capability + reply tool + instructions
|
+-- Permission relay?
    +-- Yes -> Add claude/channel/permission capability + notification handler
    +-- No  -> Skip (most channels don't need this)
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Events don't arrive | Check `/mcp` in session, look for server errors |
| "blocked by org policy" | Admin must enable `channelsEnabled` in managed settings |
| Connection refused on curl | Port not bound or stale process; `lsof -i :<port>` |
| Channel registered but silent | Verify `--dangerously-load-development-channels server:name` |
| Permission relay not working | Need Claude Code v2.1.81+, check `claude/channel/permission` declared |
