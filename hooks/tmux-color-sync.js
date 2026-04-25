#!/usr/bin/env node
// Syncs Claude Code /color to tmux status bar color.
// Runs as a Stop hook so tmux updates after /color commands.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

if (!process.env.TMUX) process.exit(0);

const CLAUDE_COLOR_TO_TMUX = {
  red: 196, blue: 33, green: 46, yellow: 226,
  purple: 129, orange: 208, pink: 199, cyan: 51,
};

let input = '';
const timeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(timeout);
  try {
    const data = JSON.parse(input);
    const jsonlPath = data.transcript_path || '';
    if (!jsonlPath || !fs.existsSync(jsonlPath)) process.exit(0);

    const content = fs.readFileSync(jsonlPath, 'utf8');
    const colorMatches = content.match(/"agentColor":"[^"]+"/g);
    if (!colorMatches || colorMatches.length === 0) process.exit(0);

    const last = colorMatches[colorMatches.length - 1];
    const m = last.match(/"agentColor":"([^"]+)"/);
    if (!m) process.exit(0);

    const agentColor = m[1];
    const color256 = agentColor === 'default' ? null : CLAUDE_COLOR_TO_TMUX[agentColor];
    if (color256 == null) process.exit(0);

    execSync(`tmux set-option -q status-style bg=colour${color256}`, {
      stdio: 'ignore', timeout: 500
    });
  } catch (e) {}
});
