#!/usr/bin/env node
// gsd-hook-version: 1.38.1
// Claude Code Statusline - GSD Edition
// Shows: datetime | model | git branch | current task (or GSD state) | directory | token usage | context bar

const fs = require('fs');
const path = require('path');
const os = require('os');

// --- GSD state reader -------------------------------------------------------

/**
 * Walk up from dir looking for .planning/STATE.md.
 * Returns parsed state object or null.
 */
function readGsdState(dir) {
  const home = os.homedir();
  let current = dir;
  for (let i = 0; i < 10; i++) {
    const candidate = path.join(current, '.planning', 'STATE.md');
    if (fs.existsSync(candidate)) {
      try {
        return parseStateMd(fs.readFileSync(candidate, 'utf8'));
      } catch (e) {
        return null;
      }
    }
    const parent = path.dirname(current);
    if (parent === current || current === home) break;
    current = parent;
  }
  return null;
}

/**
 * Parse STATE.md frontmatter + Phase line from body.
 * Returns { status, milestone, milestoneName, phaseNum, phaseTotal, phaseName }
 */
function parseStateMd(content) {
  const state = {};

  // YAML frontmatter between --- markers
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (fmMatch) {
    for (const line of fmMatch[1].split('\n')) {
      const m = line.match(/^(\w+):\s*(.+)/);
      if (!m) continue;
      const [, key, val] = m;
      const v = val.trim().replace(/^["']|["']$/g, '');
      if (key === 'status') state.status = v === 'null' ? null : v;
      if (key === 'milestone') state.milestone = v === 'null' ? null : v;
      if (key === 'milestone_name') state.milestoneName = v === 'null' ? null : v;
    }
  }

  // Phase: N of M (name)  or  Phase: none active (...)
  const phaseMatch = content.match(/^Phase:\s*(\d+)\s+of\s+(\d+)(?:\s+\(([^)]+)\))?/m);
  if (phaseMatch) {
    state.phaseNum = phaseMatch[1];
    state.phaseTotal = phaseMatch[2];
    state.phaseName = phaseMatch[3] || null;
  }

  // Fallback: parse Status: from body when frontmatter is absent
  if (!state.status) {
    const bodyStatus = content.match(/^Status:\s*(.+)/m);
    if (bodyStatus) {
      const raw = bodyStatus[1].trim().toLowerCase();
      if (raw.includes('ready to plan') || raw.includes('planning')) state.status = 'planning';
      else if (raw.includes('execut')) state.status = 'executing';
      else if (raw.includes('complet') || raw.includes('archived')) state.status = 'complete';
    }
  }

  return state;
}

/**
 * Format GSD state into display string.
 * Format: "v1.9 Code Quality · executing · fix-graphiti-deployment (1/5)"
 * Gracefully degrades when parts are missing.
 */
function formatGsdState(s) {
  const parts = [];

  // Milestone: version + name (skip placeholder "milestone")
  if (s.milestone || s.milestoneName) {
    const ver = s.milestone || '';
    const name = (s.milestoneName && s.milestoneName !== 'milestone') ? s.milestoneName : '';
    const ms = [ver, name].filter(Boolean).join(' ');
    if (ms) parts.push(ms);
  }

  // Status
  if (s.status) parts.push(s.status);

  // Phase
  if (s.phaseNum && s.phaseTotal) {
    const phase = s.phaseName
      ? `${s.phaseName} (${s.phaseNum}/${s.phaseTotal})`
      : `ph ${s.phaseNum}/${s.phaseTotal}`;
    parts.push(phase);
  }

  return parts.join(' · ');
}

// --- git branch -------------------------------------------------------------

/**
 * Read the current git branch for a given directory by parsing .git/HEAD directly.
 * Avoids spawning a child process (fast, no PATH issues).
 */
function getGitBranch(dir) {
  try {
    let current = dir;
    for (let i = 0; i < 10; i++) {
      const headPath = path.join(current, '.git', 'HEAD');
      if (fs.existsSync(headPath)) {
        const head = fs.readFileSync(headPath, 'utf8').trim();
        // ref: refs/heads/<branch>
        const m = head.match(/^ref:\s*refs\/heads\/(.+)$/);
        if (m) return m[1];
        // detached HEAD — show short hash
        if (/^[0-9a-f]{7,}$/i.test(head)) return head.slice(0, 7);
        return null;
      }
      const parent = path.dirname(current);
      if (parent === current) break;
      current = parent;
    }
  } catch (e) {}
  return null;
}

// --- token cost estimation --------------------------------------------------

// Approximate cost per 1M tokens (input / output) for known models.
// Values in USD, updated 2025-04. Used only for rough display estimates.
const MODEL_COSTS = {
  'claude-opus-4':        { in: 15,  out: 75  },
  'claude-sonnet-4':      { in: 3,   out: 15  },
  'claude-haiku-4':       { in: 0.8, out: 4   },
  'claude-3-5-sonnet':    { in: 3,   out: 15  },
  'claude-3-5-haiku':     { in: 0.8, out: 4   },
  'claude-3-opus':        { in: 15,  out: 75  },
  'claude-3-sonnet':      { in: 3,   out: 15  },
  'claude-3-haiku':       { in: 0.25,out: 1.25},
};

function estimateCost(modelId, inputTokens, outputTokens) {
  if (!modelId || (!inputTokens && !outputTokens)) return null;
  const id = modelId.toLowerCase();
  let rates = null;
  for (const key of Object.keys(MODEL_COSTS)) {
    if (id.includes(key)) { rates = MODEL_COSTS[key]; break; }
  }
  if (!rates) return null;
  const cost = (inputTokens / 1_000_000) * rates.in + (outputTokens / 1_000_000) * rates.out;
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  if (cost < 1)    return `$${cost.toFixed(3)}`;
  return `$${cost.toFixed(2)}`;
}

function formatTokens(n) {
  if (n == null) return null;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${Math.round(n / 1_000)}k`;
  return String(n);
}

// --- duration formatting ----------------------------------------------------

function formatDuration(ms) {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}h${String(m).padStart(2,'0')}m`;
  return `${m}m`;
}

// --- session tracking from JSONL conversation files -------------------------

const _sessionCache = {};

function getSessionTracking(session, transcriptPath) {
  if (!session) return { count: null, firstMessageTime: null, agentColor: null };
  try {
    const jsonlPath = transcriptPath;
    if (!jsonlPath || !fs.existsSync(jsonlPath)) return { count: null, firstMessageTime: null, agentColor: null };

    const content = fs.readFileSync(jsonlPath, 'utf8');

    // Get first user message timestamp (cached after first read)
    let firstMessageTime = _sessionCache[session] || null;
    if (firstMessageTime === null) {
      const lines = content.split('\n');
      for (const line of lines) {
        if (!line || !line.includes('"type":"user"')) continue;
        try {
          const entry = JSON.parse(line);
          if (entry.type === 'user' && entry.timestamp) {
            firstMessageTime = new Date(entry.timestamp).getTime();
            _sessionCache[session] = firstMessageTime;
            break;
          }
        } catch (e) {}
      }
    }

    // Fast string count for user messages (avoids parsing every line)
    const count = (content.match(/"type":"user"/g) || []).length;

    // Extract latest agentColor from JSONL (set by /color command)
    let agentColor = null;
    const colorMatches = content.match(/"agentColor":"[^"]+"/g);
    if (colorMatches && colorMatches.length > 0) {
      const last = colorMatches[colorMatches.length - 1];
      const m = last.match(/"agentColor":"([^"]+)"/);
      if (m) agentColor = m[1];
    }

    return { count: count || null, firstMessageTime, agentColor };
  } catch (e) {
    return { count: null, firstMessageTime: null, agentColor: null };
  }
}

// --- tmux color sync --------------------------------------------------------

const CLAUDE_COLOR_TO_TMUX = {
  red: 196, blue: 33, green: 46, yellow: 226,
  purple: 129, orange: 208, pink: 199, cyan: 51,
};

let _lastTmuxColor = null;

function syncTmuxColor(agentColor) {
  if (!process.env.TMUX) return;

  // Direction 1: Claude /color → tmux (takes priority)
  // Direction 2: TCC_COLOR env var → no action needed (already set by tcc)
  let color256 = null;
  if (agentColor && agentColor !== 'default') {
    color256 = CLAUDE_COLOR_TO_TMUX[agentColor];
  } else if (process.env.TCC_COLOR) {
    color256 = parseInt(process.env.TCC_COLOR, 10);
  }

  if (color256 == null || color256 === _lastTmuxColor) return;
  _lastTmuxColor = color256;

  try {
    require('child_process').execSync(
      `tmux set-option -q status-style bg=colour${color256}`,
      { stdio: 'ignore', timeout: 500 }
    );
  } catch (e) {}
}

function formatRelativeTime(date, now) {
  const pad = n => String(n).padStart(2, '0');
  const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfThatDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const daysAgo = Math.floor((startOfToday - startOfThatDay) / (24 * 60 * 60 * 1000));
  if (daysAgo === 0) return time;
  return `${daysAgo}d ago ${time}`;
}

// --- stdin ------------------------------------------------------------------

function runStatusline() {
  let input = '';
  // Timeout guard: if stdin doesn't close within 3s (e.g. pipe issues on
  // Windows/Git Bash), exit silently instead of hanging. See #775.
  const stdinTimeout = setTimeout(() => process.exit(0), 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const model = data.model?.display_name || 'Claude';
    const modelId = data.model?.id || '';
    const dir = data.workspace?.current_dir || process.cwd();
    const session = data.session_id || '';
    const remaining = data.context_window?.remaining_percentage;

    // --- session tracking (first message time, count, last message time) ---
    const now = new Date();
    const transcriptPath = data.transcript_path || '';
    const { count: msgCount, firstMessageTime, agentColor } = getSessionTracking(session, transcriptPath);

    syncTmuxColor(agentColor);

    const lastMsgStr = formatRelativeTime(now, now);
    let startStr = '';
    let durationStr = '';
    if (firstMessageTime != null) {
      const firstMsg = new Date(firstMessageTime);
      startStr = formatRelativeTime(firstMsg, now);
      const elapsed = now.getTime() - firstMessageTime;
      if (elapsed > 0) durationStr = formatDuration(elapsed);
    }

    // --- vim mode ---
    let vimMode = '';
    if (data.vim?.mode) {
      const modeColors = {
        'NORMAL':      '\x1b[32m',  // green
        'INSERT':      '\x1b[34m',  // blue
        'VISUAL':      '\x1b[35m',  // magenta
        'VISUAL LINE': '\x1b[35m',
      };
      const col = modeColors[data.vim.mode] || '\x1b[37m';
      vimMode = ` ${col}[${data.vim.mode}]\x1b[0m │`;
    }

    // Context window display (shows USED percentage scaled to usable context)
    // Claude Code reserves a buffer for autocompact. By default this is ~16.5%
    // of the total window, but users can override it via CLAUDE_CODE_AUTO_COMPACT_WINDOW
    // (a token count). When the env var is set, compute the buffer % dynamically so
    // the meter correctly reflects early-compaction configurations (#2219).
    const totalCtx = data.context_window?.total_tokens || 1_000_000;
    const acw = parseInt(process.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW || '0', 10);
    const AUTO_COMPACT_BUFFER_PCT = acw > 0
      ? Math.min(100, (acw / totalCtx) * 100)
      : 16.5;
    let ctx = '';
    let usedPct = null;
    if (remaining != null) {
      // Normalize: subtract buffer from remaining, scale to usable range
      const usableRemaining = Math.max(0, ((remaining - AUTO_COMPACT_BUFFER_PCT) / (100 - AUTO_COMPACT_BUFFER_PCT)) * 100);
      usedPct = Math.max(0, Math.min(100, Math.round(100 - usableRemaining)));

      // Write context metrics to bridge file for the context-monitor PostToolUse hook.
      // The monitor reads this file to inject agent-facing warnings when context is low.
      // Reject session IDs with path separators or traversal sequences to prevent
      // a malicious session_id from writing files outside the temp directory.
      const sessionSafe = session && !/[/\\]|\.\./.test(session);
      if (sessionSafe) {
        try {
          const bridgePath = path.join(os.tmpdir(), `claude-ctx-${session}.json`);
          const bridgeData = JSON.stringify({
            session_id: session,
            remaining_percentage: remaining,
            used_pct: usedPct,
            timestamp: Math.floor(Date.now() / 1000)
          });
          fs.writeFileSync(bridgePath, bridgeData);
        } catch (e) {
          // Silent fail -- bridge is best-effort, don't break statusline
        }
      }

      // Build progress bar (10 segments)
      const filled = Math.floor(usedPct / 10);
      const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);

      // Color based on usable context thresholds
      if (usedPct < 50) {
        ctx = ` \x1b[32m${bar} ${usedPct}%\x1b[0m`;
      } else if (usedPct < 65) {
        ctx = ` \x1b[33m${bar} ${usedPct}%\x1b[0m`;
      } else if (usedPct < 80) {
        ctx = ` \x1b[38;5;208m${bar} ${usedPct}%\x1b[0m`;
      } else {
        ctx = ` \x1b[5;31m💀 ${bar} ${usedPct}%\x1b[0m`;
      }
    }

    // --- token usage + cost (commented out — keeping context bar only) ---
    let tokenStr = '';
    // const ctxWin = data.context_window;
    // const totalIn  = ctxWin?.total_input_tokens;
    // const totalOut = ctxWin?.total_output_tokens;
    // const ctxSize  = ctxWin?.context_window_size;
    // const curUsage = ctxWin?.current_usage;
    // const curIn    = curUsage?.input_tokens;
    // const curOut   = curUsage?.output_tokens;
    // const cacheRead = curUsage?.cache_read_input_tokens;
    //
    // if (totalIn != null || totalOut != null) {
    //   const parts = [];
    //   if (totalIn  != null) parts.push(`in:${formatTokens(totalIn)}`);
    //   if (totalOut != null) parts.push(`out:${formatTokens(totalOut)}`);
    //   if (ctxSize  != null && curIn != null) {
    //     parts.push(`ctx:${formatTokens(curIn)}/${formatTokens(ctxSize)}`);
    //   }
    //   if (cacheRead != null && cacheRead > 0) parts.push(`cache:${formatTokens(cacheRead)}`);
    //   const cost = estimateCost(modelId, totalIn, totalOut);
    //   if (cost) parts.push(`\x1b[33m~${cost}\x1b[0m`);
    //   if (parts.length > 0) tokenStr = ` \x1b[2m[${parts.join(' ')}]\x1b[0m`;
    // }

    // --- cost (from Claude Code's own tracking) ---
    const totalCostUsd = data.cost?.total_cost_usd;
    if (totalCostUsd != null && totalCostUsd > 0) {
      const costFmt = totalCostUsd < 0.01 ? `$${totalCostUsd.toFixed(4)}`
                     : totalCostUsd < 1    ? `$${totalCostUsd.toFixed(3)}`
                     : `$${totalCostUsd.toFixed(2)}`;
      tokenStr = ` \x1b[33m~${costFmt}\x1b[0m`;
    }

    // --- lines added/removed ---
    let linesStr = '';
    const linesAdded = data.cost?.total_lines_added;
    const linesRemoved = data.cost?.total_lines_removed;
    if ((linesAdded != null && linesAdded > 0) || (linesRemoved != null && linesRemoved > 0)) {
      const parts = [];
      if (linesAdded > 0) parts.push(`\x1b[32m+${linesAdded}\x1b[0m`);
      if (linesRemoved > 0) parts.push(`\x1b[31m-${linesRemoved}\x1b[0m`);
      linesStr = ` \x1b[2m[${parts.join('/')}]\x1b[0m`;
    }

    // --- rate limits (Claude.ai subscriptions) ---
    let rateLimitStr = '';
    const rl = data.rate_limits;
    if (rl) {
      const parts = [];
      if (rl.five_hour?.used_percentage != null) {
        const pct = Math.round(rl.five_hour.used_percentage);
        const col = pct > 80 ? '\x1b[31m' : pct > 50 ? '\x1b[33m' : '\x1b[32m';
        parts.push(`${col}5h:${pct}%\x1b[0m`);
      }
      if (rl.seven_day?.used_percentage != null) {
        const pct = Math.round(rl.seven_day.used_percentage);
        const col = pct > 80 ? '\x1b[31m' : pct > 50 ? '\x1b[33m' : '\x1b[32m';
        parts.push(`${col}7d:${pct}%\x1b[0m`);
      }
      if (parts.length > 0) rateLimitStr = ` \x1b[2m[${parts.join(' ')}\x1b[2m]\x1b[0m`;
    }

    // Current task from todos
    let task = '';
    const homeDir = os.homedir();
    // Respect CLAUDE_CONFIG_DIR for custom config directory setups (#870)
    const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(homeDir, '.claude');
    const todosDir = path.join(claudeDir, 'todos');
    if (session && fs.existsSync(todosDir)) {
      try {
        const files = fs.readdirSync(todosDir)
          .filter(f => f.startsWith(session) && f.includes('-agent-') && f.endsWith('.json'))
          .map(f => ({ name: f, mtime: fs.statSync(path.join(todosDir, f)).mtime }))
          .sort((a, b) => b.mtime - a.mtime);

        if (files.length > 0) {
          try {
            const todos = JSON.parse(fs.readFileSync(path.join(todosDir, files[0].name), 'utf8'));
            const inProgress = todos.find(t => t.status === 'in_progress');
            if (inProgress) task = inProgress.activeForm || '';
          } catch (e) {}
        }
      } catch (e) {
        // Silently fail on file system errors - don't break statusline
      }
    }

    // GSD state (milestone · status · phase) — shown when no todo task
    const gsdStateStr = task ? '' : formatGsdState(readGsdState(dir) || {});

    // GSD update available? (disabled — removed from statusline output)
    // let gsdUpdate = '';
    // const sharedCacheFile = path.join(homeDir, '.cache', 'gsd', 'gsd-update-check.json');
    // const legacyCacheFile = path.join(claudeDir, 'cache', 'gsd-update-check.json');
    // const cacheFile = fs.existsSync(sharedCacheFile) ? sharedCacheFile : legacyCacheFile;
    // if (fs.existsSync(cacheFile)) {
    //   try {
    //     const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    //     if (cache.update_available) {
    //       gsdUpdate = '\x1b[33m⬆ /gsd-update\x1b[0m │ ';
    //     }
    //     if (cache.stale_hooks && cache.stale_hooks.length > 0) {
    //       const isDevInstall = (() => {
    //         if (!cache.installed || !cache.latest || cache.latest === 'unknown') return false;
    //         const parseV = v => v.replace(/^v/, '').split('.').map(Number);
    //         const [ai, bi, ci] = parseV(cache.installed);
    //         const [an, bn, cn] = parseV(cache.latest);
    //         return ai > an || (ai === an && bi > bn) || (ai === an && bi === bn && ci > cn);
    //       })();
    //       if (isDevInstall) {
    //         gsdUpdate += '\x1b[33m⚠ dev install — re-run installer to sync hooks\x1b[0m │ ';
    //       } else {
    //         gsdUpdate += '\x1b[31m⚠ stale hooks — run /gsd-update\x1b[0m │ ';
    //       }
    //     }
    //   } catch (e) {}
    // }

    // --- git branch ---
    const branch = getGitBranch(dir);

    // --- agent badge ---
    let agentStr = '';
    if (data.agent?.name) {
      agentStr = ` \x1b[35m[${data.agent.name}]\x1b[0m │`;
    }

    // Output
    const dirname = path.basename(dir);
    const middle = task
      ? `\x1b[1m${task}\x1b[0m`
      : gsdStateStr
        ? `\x1b[2m${gsdStateStr}\x1b[0m`
        : null;

    // Build the full statusline:
    // model | [VIM MODE] | agent | task/gsd | dirname (branch) | ctx bar | cost | lines | rate limits | started HH:MM │ last HH:MM:SS │ duration │ #msgs
    const modelStr = `\x1b[2m${model}\x1b[0m`;

    // dirname (branch)
    const dirBranchStr = branch
      ? `\x1b[2m${dirname}\x1b[0m \x1b[2m(\x1b[36m${branch}\x1b[0m\x1b[2m)\x1b[0m`
      : `\x1b[2m${dirname}\x1b[0m`;

    // Time block at far right: "started 1d ago 16:06, last 16:06, 24h, #59"
    const timeParts = [];
    if (startStr) timeParts.push(`started ${startStr}`);
    timeParts.push(`last ${lastMsgStr}`);
    if (durationStr) timeParts.push(durationStr);
    if (msgCount != null) timeParts.push(`#${msgCount}`);
    const timeBlock = `\x1b[2m${timeParts.join(', ')}\x1b[0m`;

    let line = ``;
    line += `${dirBranchStr}`;
    if (vimMode)  line += ` │${vimMode}`;
    if (agentStr) line += agentStr;
    if (middle)   line += ` │ ${middle}`;
    line += ` │ ${modelStr}`;
    line += ctx;
    // line += tokenStr;
    line += linesStr;
    // line += rateLimitStr;
    line += ` │ ${timeBlock}`;

    process.stdout.write(line);
  } catch (e) {
    // Silent fail - don't break statusline on parse errors
  }
});
}

// Export helpers for unit tests. Harmless when run as a script.
module.exports = { readGsdState, parseStateMd, formatGsdState };

if (require.main === module) runStatusline();
