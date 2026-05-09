#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { z } from 'zod'

const WAHA_API_URL = process.env.WAHA_API_URL || 'https://waha.fhijazi.com'
const WAHA_API_KEY = process.env.WAHA_API_KEY || ''
const WAHA_SESSION = process.env.WAHA_SESSION || 'default'
const WAHA_ALLOWED_CHATS = (process.env.WAHA_ALLOWED_CHATS || '').split(',').filter(Boolean)
const WEBHOOK_PORT = parseInt(process.env.WAHA_WEBHOOK_PORT || '8789', 10)

async function wahaFetch(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${WAHA_API_URL}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': WAHA_API_KEY,
      ...(opts.headers || {}),
    },
  })
  return res.json()
}

async function sendText(chatId: string, text: string, replyTo?: string) {
  const body: Record<string, unknown> = { session: WAHA_SESSION, chatId, text }
  if (replyTo) body.reply_to = replyTo
  return wahaFetch('/api/sendText', { method: 'POST', body: JSON.stringify(body) })
}

const mcp = new Server(
  { name: 'waha', version: '0.1.0' },
  {
    capabilities: {
      experimental: {
        'claude/channel': {},
        'claude/channel/permission': {},
      },
      tools: {},
    },
    instructions: [
      'WhatsApp messages arrive as <channel source="waha" chat_id="..." sender="..." sender_name="...">.',
      'Reply with the waha_reply tool, passing the chat_id from the tag.',
      'For replies to a specific message, also pass message_id.',
      'Chat IDs ending in @c.us are individuals, @g.us are groups.',
      'Keep replies concise — WhatsApp messages should be short and readable on mobile.',
    ].join(' '),
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'waha_reply',
      description: 'Send a WhatsApp message via WAHA',
      inputSchema: {
        type: 'object' as const,
        properties: {
          chat_id: { type: 'string', description: 'WhatsApp chat ID (e.g. 12345@c.us or 12345@g.us)' },
          text: { type: 'string', description: 'Message text to send' },
          message_id: { type: 'string', description: 'Optional: reply to this specific message ID' },
        },
        required: ['chat_id', 'text'],
      },
    },
    {
      name: 'waha_send_seen',
      description: 'Mark a WhatsApp chat as read/seen',
      inputSchema: {
        type: 'object' as const,
        properties: {
          chat_id: { type: 'string', description: 'WhatsApp chat ID' },
        },
        required: ['chat_id'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params
  if (name === 'waha_reply') {
    const { chat_id, text, message_id } = args as { chat_id: string; text: string; message_id?: string }
    const result = await sendText(chat_id, text, message_id)
    return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
  }
  if (name === 'waha_send_seen') {
    const { chat_id } = args as { chat_id: string }
    const result = await wahaFetch('/api/sendSeen', {
      method: 'POST',
      body: JSON.stringify({ session: WAHA_SESSION, chatId: chat_id }),
    })
    return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
  }
  throw new Error(`unknown tool: ${name}`)
})

const PermissionRequestSchema = z.object({
  method: z.literal('notifications/claude/channel/permission_request'),
  params: z.object({
    request_id: z.string(),
    tool_name: z.string(),
    description: z.string(),
    input_preview: z.string(),
  }),
})

mcp.setNotificationHandler(PermissionRequestSchema, async ({ params }) => {
  if (WAHA_ALLOWED_CHATS.length === 0) return
  const target = WAHA_ALLOWED_CHATS[0]
  await sendText(
    target,
    `🔐 Claude wants to run *${params.tool_name}*:\n${params.description}\n\nReply "yes ${params.request_id}" or "no ${params.request_id}"`,
  )
})

const PERMISSION_REPLY_RE = /^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$/i

await mcp.connect(new StdioServerTransport())

Bun.serve({
  port: WEBHOOK_PORT,
  hostname: '127.0.0.1',
  async fetch(req) {
    if (req.method !== 'POST') return new Response('method not allowed', { status: 405 })

    try {
      const event = await req.json()

      if (event.event !== 'message' && event.event !== 'message.any') {
        return new Response('ignored')
      }

      const payload = event.payload
      if (!payload || payload.fromMe) return new Response('ignored')

      const chatId = payload.from || ''
      const senderId = payload.participant || payload.from || ''

      if (WAHA_ALLOWED_CHATS.length > 0 && !WAHA_ALLOWED_CHATS.includes(chatId) && !WAHA_ALLOWED_CHATS.includes(senderId)) {
        return new Response('forbidden', { status: 403 })
      }

      const body = payload.body || ''

      const m = PERMISSION_REPLY_RE.exec(body)
      if (m) {
        await mcp.notification({
          method: 'notifications/claude/channel/permission',
          params: {
            request_id: m[2].toLowerCase(),
            behavior: m[1].toLowerCase().startsWith('y') ? 'allow' : 'deny',
          },
        })
        return new Response('verdict recorded')
      }

      const senderName = payload._data?.notifyName || payload.from || 'unknown'
      const meta: Record<string, string> = {
        chat_id: chatId,
        sender: senderId,
        sender_name: senderName,
        message_id: payload.id || '',
      }
      if (payload.hasMedia && payload.media?.url) {
        meta.media_url = payload.media.url
        meta.media_type = payload.media.mimetype || ''
      }

      let content = body
      if (payload.hasMedia && !body) {
        content = `[media: ${payload.media?.mimetype || 'unknown'}]`
      }

      await mcp.notification({
        method: 'notifications/claude/channel',
        params: { content, meta },
      })

      return new Response('ok')
    } catch (e) {
      return new Response('parse error', { status: 400 })
    }
  },
})
