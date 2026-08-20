# GitHub Actions Full Production Validation (2026-08-20)

## Summary
Successfully deployed and validated the complete 6-job GitHub Actions workflow for daily stock analysis pipeline.

## Workflow Configuration
**File**: `.github/workflows/daily-stock.yml` (at repo root — critical!)
**Jobs**: 6 (integrated-analysis, news-filtering, skill-hub-monitoring, obsidian-organize, technical-signal-snapshot, summary)
**Schedules**: 4 cron expressions (07:00, 09:30, 10:00, 02:00 KST) + workflow_dispatch
**Model Selection**:
- integrated-analysis: Google Gemini direct (gemini-2.5-flash) — free, no credits
- All other jobs: NVIDIA NIM 550B (nemotron-3-ultra-550b-a55b) with 70B fallback

## Required GitHub Secrets (5)
| Secret | Source |
|--------|--------|
| GOOGLE_API_KEY | Google AI Studio |
| TELEGRAM_BOT_TOKEN | @BotFather |
| TELEGRAM_CHAT_ID | User chat ID (6723387878) |
| NVIDIA_API_KEY | https://build.nvidia.com |
| OPENROUTER_API_KEY | Optional fallback |

## Validation Results

### Infrastructure
- ✅ Hermes installation on ubuntu-latest works
- ✅ Python 3.11 via actions/setup-python@v5 (system Python 3.14 incompatible with numpy)
- ✅ Playwright browser engine installs (for web_search if needed)
- ✅ Ripgrep + ffmpeg installed

### Job Execution
- ✅ `obsidian-organize` job ran on schedule (02:00 KST) — completed in 1m 44s
- ✅ `workflow_dispatch` manual trigger works with `job_type` input
- ✅ All 6 jobs trigger correctly based on `job_type` filter
- ✅ **Full manual run (all jobs)**: All 6 jobs completed successfully

### Model Selection (Critical Finding)
- ❌ **Previous**: `meta-llama/llama-3.1-8b-instruct:free` — no longer free on OpenRouter (HTTP 404)
- ✅ **Fixed**: Google Gemini direct for fundamental (free tier, no API credits consumed)
- ✅ **Fixed**: NVIDIA NIM 550B with 70B fallback for technical/news/skillhub/obsidian

### Git Integration
- ✅ `permissions: contents: write` + `actions: read` required for git push
- ✅ github-actions[bot] commits reports to `주식분석/` directory
- ✅ Local `git pull origin main` syncs reports to Obsidian vault

### Telegram Delivery
- ✅ appleboy/telegram-action works
- ✅ message_id 30 delivered successfully
- ✅ Korean messages render correctly

## Key Pitfalls Discovered

1. **Repo root confusion**: `git rev-parse --show-toplevel` returns `C:/Users/kho` not `C:/Users/kho/github/khyo114`. Workflow file must be at `.github/workflows/` relative to actual repo root.

2. **Nested workflow paths ignored**: `github/khyo114/.github/workflows/daily-stock.yml` is NOT scanned by GitHub Actions. Must be at `.github/workflows/daily-stock.yml`.

3. **Free model deprecation**: OpenRouter free models change frequently. Google Gemini direct API is stable free tier. NVIDIA NIM requires API key but has monthly free credit reset (1st 00:00 UTC).

4. **Python version pinning**: GitHub runners have Python 3.14 system default. Must explicitly use `actions/setup-python@v5` with `python-version: '3.11'` for numpy/pandas compatibility.

5. **Model drift prevention**: Each job explicitly sets model/provider in steps — no reliance on config.yaml which may drift.

6. **Workflow dispatch input**: Must define `inputs:` under `workflow_dispatch:` for manual trigger to show dropdown options.

## Next Steps
1. Monitor tomorrow's scheduled runs (2026-08-21 02:00, 07:00, 09:30, 10:00 KST)
2. Verify local cron jobs (30-min intraday) work when PC is on
3. Externalize watchlist to `config/watchlist.yaml` (planned)
4. Add local WSL cron for intraday 30-min signals as backup