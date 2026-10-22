// Reference Remotion primitives for PR explainers (see "PR explainers" in SKILL.md).
// Copy this file into the video project and feed it the PR's real components; never ship the example data.
// Everything is drawn in one 1080x1920 SVG so node coordinates are canvas pixels. Keep nodes, badges and
// labels inside SAFE (the feed's overlay-safe box) and captions inside the caption band.
import React from 'react'
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'

export const SAFE = { left: 160, right: 820, top: 220, bottom: 1120, captionTop: 1180, captionBottom: 1300 }
export const C = {
  bg: '#0b1020', node: '#1e293b', text: '#e2e8f0', dim: '#334155',
  change: '#22d3ee', risk: '#f43f5e', touched: '#f59e0b', safe: '#64748b', decision: '#facc15',
}

export type Node = { id: string; label: string; x: number; y: number; sub?: string }
export type Hop = { from: string; to: string; label?: string; bend?: number }
/** How a node reads right now: plain, dimmed, part of the change, hit by the blast radius, or out of reach. */
export type Tone = 'plain' | 'dim' | 'changed' | 'risk' | 'touched' | 'safe'
const toneColor: Record<Tone, string> = { plain: C.text, dim: C.dim, changed: C.change, risk: C.risk, touched: C.touched, safe: C.safe }
const toneTag: Partial<Record<Tone, string>> = { changed: 'CHANGED', risk: 'AT RISK', touched: 'TOUCHED', safe: 'SAFE' }

const usePop = (at: number) => {
  const frame = useCurrentFrame(), { fps } = useVideoConfig()
  return spring({ frame: frame - at, fps, config: { damping: 11, stiffness: 170 } })
}

/** Quadratic curve between two nodes, bent sideways so edges are never a flat chain. */
export const curve = (a: Node, b: Node, bend = 0.22) => {
  const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y
  const cx = mx - dy * bend, cy = my + dx * bend
  const at = (t: number) => ({ x: (1 - t) ** 2 * a.x + 2 * (1 - t) * t * cx + t * t * b.x, y: (1 - t) ** 2 * a.y + 2 * (1 - t) * t * cy + t * t * b.y })
  return { d: `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`, at }
}

/** Big act title ("1 · NOW", "2 · THE CHANGE", "3 · BLAST RADIUS") at the top of the safe box. */
export const ActTitle: React.FC<{ n: number; title: string; color: string; at?: number }> = ({ n, title, color, at = 0 }) => {
  const p = usePop(at)
  return (
    <g opacity={p} transform={`translate(${(SAFE.left + SAFE.right) / 2} ${SAFE.top + 40}) scale(${0.8 + 0.2 * p})`}>
      <circle cx={-250} cy={-14} r={30} fill={color} />
      <text x={-250} y={-3} textAnchor="middle" fontSize={34} fontWeight={900} fill={C.bg}>{n}</text>
      <text x={-200} y={0} fontSize={46} fontWeight={800} fill={color} letterSpacing={2}>{title}</text>
    </g>
  )
}

/** Round glowing node; tone colours it and, for change/risk tones, a tag pops above it. */
export const NodeDot: React.FC<{ node: Node; tone?: Tone; at?: number; r?: number }> = ({ node, tone = 'plain', at = 0, r = 58 }) => {
  const p = usePop(at), color = toneColor[tone], tag = toneTag[tone]
  return (
    <g opacity={p} transform={`translate(${node.x} ${node.y}) scale(${p})`}>
      {tone !== 'dim' && <circle r={r + 16} fill={color} opacity={0.18} />}
      <circle r={r} fill={C.node} stroke={color} strokeWidth={tone === 'plain' || tone === 'dim' ? 4 : 9} />
      <text y={r + 46} textAnchor="middle" fontSize={34} fontWeight={700} fill={tone === 'dim' ? C.dim : C.text}>{node.label}</text>
      {node.sub && <text y={r + 84} textAnchor="middle" fontSize={26} fill={tone === 'dim' ? C.dim : '#94a3b8'}>{node.sub}</text>}
      {tag && (
        <g transform={`translate(0 ${-r - 34})`}>
          <rect x={-78} y={-24} width={156} height={44} rx={22} fill={color} />
          <text y={8} textAnchor="middle" fontSize={24} fontWeight={900} fill={C.bg}>{tag}</text>
        </g>
      )}
    </g>
  )
}

/** Numbered badge (1, 2, 3...) that springs in on a hop. */
export const StepBadge: React.FC<{ n: number; x: number; y: number; at: number; color?: string }> = ({ n, x, y, at, color = C.decision }) => {
  const p = usePop(at)
  if (p <= 0.001) return null
  return (
    <g transform={`translate(${x} ${y}) scale(${p})`}>
      <circle r={30} fill={color} stroke={C.bg} strokeWidth={5} />
      <text y={12} textAnchor="middle" fontSize={34} fontWeight={900} fill={C.bg}>{n}</text>
    </g>
  )
}

/**
 * A sequence (e.g. frontend -> auth -> backend -> database): hop i draws its edge, a packet rides it, and its
 * step number pops on the edge as the packet passes, strictly in order. Numbers stay for the rest of the scene.
 * Render it BEFORE the NodeDots so nodes cover the edge ends; flip a hop's `bend` sign if its badge lands on a label.
 */
export const StepFlow: React.FC<{ nodes: Node[]; hops: Hop[]; start: number; every?: number; color?: string; highlight?: string[] }> = ({ nodes, hops, start, every = 24, color = C.text, highlight = [] }) => {
  const frame = useCurrentFrame()
  const byId = Object.fromEntries(nodes.map(n => [n.id, n]))
  return (
    <g>
      {hops.map((hop, i) => {
        const { d, at } = curve(byId[hop.from], byId[hop.to], hop.bend)
        const t0 = start + i * every, draw = interpolate(frame, [t0, t0 + every * 0.6], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
        const ride = interpolate(frame, [t0, t0 + every], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
        const mid = at(0.5), packet = at(ride), hot = highlight.includes(`${hop.from}>${hop.to}`)
        const stroke = hot ? C.change : color
        return (
          <g key={i}>
            <path d={d} fill="none" stroke={stroke} strokeWidth={hot ? 9 : 5} strokeLinecap="round" opacity={0.8} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />
            {ride > 0 && ride < 1 && <circle cx={packet.x} cy={packet.y} r={14} fill={stroke} />}
            <StepBadge n={i + 1} x={mid.x} y={mid.y} at={t0 + every * 0.5} color={hot ? C.change : C.decision} />
            {hop.label && draw > 0.9 && <text x={mid.x + 44} y={mid.y + 10} fontSize={26} fill="#cbd5e1">{hop.label}</text>}
          </g>
        )
      })}
    </g>
  )
}

/** Ripple rings spreading from the changed node: the blast radius. Pair with blastTone() for the nodes it reaches. */
export const BlastRings: React.FC<{ center: Node; at: number; reach: number; color?: string }> = ({ center, at, reach, color = C.risk }) => {
  const frame = useCurrentFrame()
  return (
    <g>
      {[0, 1, 2].map(k => {
        const t = interpolate(frame, [at + k * 10, at + k * 10 + 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
        return t > 0 && <circle key={k} cx={center.x} cy={center.y} r={60 + t * reach} fill="none" stroke={color} strokeWidth={6 - k * 1.5} opacity={(1 - t) * 0.85 + 0.15 * (k === 0 ? 1 : 0)} />
      })}
    </g>
  )
}

/** A node turns its blast tone once the first ring has reached it (rings grow ~reach px over 40 frames). */
export const blastTone = (frame: number, center: Node, node: Node, at: number, reach: number, tone: Tone): Tone =>
  frame >= at + 40 * Math.min(1, Math.hypot(node.x - center.x, node.y - center.y) / reach) ? tone : 'plain'

/**
 * Spotlight on the exact place the reviewer decides: everything else dims, a pulsing ring marks the spot,
 * a DECISION tag beside it names it and the decision sentence sits in the safe box. Hold it at least 2 s.
 * Centre the hole on the node AND its label (e.g. y + 30, r 150) so the reviewer can read what is being decided.
 */
export const DecisionSpotlight: React.FC<{ x: number; y: number; r?: number; at: number; tag?: string; text: string; textY?: number }> = ({ x, y, r = 110, at, tag = 'DECISION', text, textY = 900 }) => {
  const frame = useCurrentFrame(), p = usePop(at)
  if (p <= 0.001) return null
  const pulse = 1 + 0.08 * Math.sin((frame - at) / 4)
  return (
    <AbsoluteFill>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%">
        <defs>
          <mask id="decision-hole">
            <rect width={1080} height={1920} fill="white" />
            <circle cx={x} cy={y} r={r * p} fill="black" />
          </mask>
        </defs>
        <rect width={1080} height={1920} fill="#000" opacity={0.62 * p} mask="url(#decision-hole)" />
        <circle cx={x} cy={y} r={r * pulse} fill="none" stroke={C.decision} strokeWidth={10} opacity={p} />
        <g transform={`translate(${x + r + 24} ${y}) scale(${p})`}>
          <rect x={0} y={-30} width={208} height={54} rx={27} fill={C.decision} />
          <text x={104} y={8} textAnchor="middle" fontSize={30} fontWeight={900} fill={C.bg}>{tag}</text>
        </g>
      </svg>
      <div style={{
        position: 'absolute', left: SAFE.left, width: SAFE.right - SAFE.left, top: textY, opacity: p,
        border: `4px solid ${C.decision}`, borderRadius: 24, background: 'rgba(11,16,32,.92)', padding: '18px 24px',
        color: C.text, fontSize: 34, fontWeight: 700, lineHeight: 1.25, fontFamily: 'Inter, system-ui, sans-serif',
      }}>{text}</div>
    </AbsoluteFill>
  )
}

/** Burned-in caption inside the caption band (y1180-1300). */
export const Caption: React.FC<{ text: string }> = ({ text }) => (
  <div style={{
    position: 'absolute', left: SAFE.left, width: SAFE.right - SAFE.left, top: SAFE.captionTop, height: SAFE.captionBottom - SAFE.captionTop,
    display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#fff', fontSize: 38, fontWeight: 800,
    lineHeight: 1.15, textShadow: '0 3px 10px #000', fontFamily: 'Inter, system-ui, sans-serif',
  }}>{text}</div>
)

/** One chapter of the video, in frames; each has its own color (e.g. Context, Before, The change, After, Blast radius, Decision). */
export type Chapter = { name: string; from: number; frames: number; color: string }

/**
 * Chapter progress line between the content (ends y1120) and the captions (y1180): one segment per chapter sized by its
 * length and filling as it plays, the current chapter's name in its own color (it pops when a chapter starts) and the
 * time left. Render it once, outside the scene Sequences, so it spans the whole video.
 */
export const ChapterBar: React.FC<{ chapters: Chapter[]; total: number }> = ({ chapters, total }) => {
  const frame = useCurrentFrame(), { fps } = useVideoConfig()
  const current = chapters.findLast(c => frame >= c.from) ?? chapters[0]
  const pop = spring({ frame: frame - current.from, fps, config: { damping: 12, mass: 0.6 } })
  const left = Math.max(0, Math.ceil((total - frame) / fps)), gap = 8, width = SAFE.right - SAFE.left - gap * (chapters.length - 1)
  return (
    <div style={{ position: 'absolute', left: SAFE.left, top: SAFE.bottom - 4, width: SAFE.right - SAFE.left, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <span style={{ fontSize: 26, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase', color: current.color, display: 'inline-block', transform: `scale(${0.8 + pop * 0.2})`, transformOrigin: 'left center' }}>{current.name}</span>
        <span style={{ fontSize: 24, color: C.safe, fontVariantNumeric: 'tabular-nums' }}>{Math.floor(left / 60)}:{String(left % 60).padStart(2, '0')} left</span>
      </div>
      <div style={{ display: 'flex', gap }}>
        {chapters.map(c => {
          const done = interpolate(frame, [c.from, c.from + c.frames], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
          const active = c === current
          return (
            <div key={c.from} style={{ width: (c.frames / total) * width, height: active ? 12 : 8, marginTop: active ? 0 : 2, borderRadius: 6, background: `${c.color}38`, overflow: 'hidden', boxShadow: active ? `0 0 16px ${c.color}b3` : 'none' }}>
              <div style={{ width: `${done * 100}%`, height: '100%', background: c.color }} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Full-frame SVG canvas in 1080x1920 coordinates for the primitives above. */
export const Canvas: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: C.bg, fontFamily: 'Inter, system-ui, sans-serif' }}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%">{children}</svg>
  </AbsoluteFill>
)
