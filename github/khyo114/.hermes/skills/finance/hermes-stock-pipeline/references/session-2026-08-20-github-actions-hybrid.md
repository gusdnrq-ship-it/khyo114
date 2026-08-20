# Session: 2026-08-20 — GitHub Actions Workflow Creation & Hybrid Architecture

## Context
User wants fully automated daily stock analysis pipeline that runs even when PC is off. Previously only local Hermes cron jobs on WSL (requires PC on). Decision: GitHub Actions for daily batch jobs + Local WSL for intraday technical signals.

## What Was Done

### 1. Created Production GitHub Actions Workflow (`.github/workflows/daily-stock.yml`)
- **5 parallel jobs** covering complete pipeline:
  - `integrated-analysis` (09:30 KST) — Fundamental + Technical
  - `news-filtering` (07:00 KST) — 92 tickers news/disclosure filtering
  - `skill-hub-monitoring` (10:00 KST) — Hermes skill hub scan
  - `obsidian-organize` (02:00 KST) — Vault structure/tag/link maintenance
  - `technical-signal-snapshot` (09:30 KST) — Daily snapshot (intraday 30-min runs locally)
  - `summary` — Combined Telegram notification

- **Key features:**
  - Explicit model/provider per job (no model drift)
  - NVIDIA NIM with 70B fallback for overloaded 550B
  - Google Gemini direct (free, no OpenRouter credits)
  - Git commit/push for Obsidian sync (reports in repo)
  - `workflow_dispatch` with `job_type` input for manual runs

### 2. Fixed Model Configuration Issues
- **Problem:** OpenRouter `meta-llama/llama-3.1-8b-instruct:free` no longer free (HTTP 404)
- **Fix:** Use Google `gemini-2.5-flash` direct (free tier) for fundamental job
- **NVIDIA:** `nvidia/nemotron-3-ultra-550b-a55b` primary, `nvidia/llama-3.1-nemotron-70b-instruct` fallback

### 3. Added Watchlist Externalization Template
- `templates/watchlist.yaml` — single source of truth for all tickers
- Separates fundamental/technical/news lists
- Documents yfinance unsupported tickers (3: 453830, 046970, 225460)

### 4. Hybrid Architecture Decision

| Layer | Jobs | Why |
|-------|------|-----|
| **GitHub Actions** | Daily batch (07:00, 09:30, 10:00, 02:00 KST) | Runs 24/7 free, PC independent |
| **Local WSL Cron** | Intraday technical (09:00–15:30 every 30min) | Sub-hour cron not reliable in GitHub Actions |
| **Obsidian Sync** | GitHub → Local `git pull` | Reports committed to repo, pulled for local Obsidian |

### 5. Secrets Required (GitHub Settings → Secrets → Actions)
```
GOOGLE_API_KEY        # Google AI Studio (aistudio.google.com)
TELEGRAM_BOT_TOKEN    # @BotFather
TELEGRAM_CHAT_ID      # 6723387878
NVIDIA_API_KEY        # build.nvidia.com
OPENROUTER_API_KEY    # Optional fallback
```

## Issues Encountered & Fixes

| Issue | Fix |
|-------|-----|
| OpenRouter free model 404 | Switch to Google Gemini direct |
| NVIDIA 550B overload | Add 70B fallback in workflow config |
| Model drift error in cron | Explicit `--model`/`--provider` in each job |
| Telegram "platform not configured" | Cached error — ignore if gateway running |
| Korean encoding on Windows | `LANG=C.UTF-8` not `ko_KR.UTF-8` |
| GitHub Actions can't access local paths | Commit/push reports to repo instead |

## Test Status
- Workflow YAML syntax validated ✅
- Cron expressions valid ✅
- Action references standard ✅
- Secret references complete ✅
- **Pending:** User to add Secrets and run `workflow_dispatch` test

## Files Created/Updated
- `references/github-actions-daily-stock.yml` — Full workflow template
- `templates/watchlist.yaml` — Ticker configuration template
- SKILL.md updated with hybrid architecture, watchlist externalization, production workflow

## Next Steps
1. User adds 5 Secrets to GitHub repo
2. Run workflow via Actions tab → `Run workflow` → `all`
3. Verify Telegram notifications + GitHub repo commits
4. Set up local `git pull` cron for Obsidian sync
5. Externalize tickers from prompts to `config/watchlist.yaml` in repo