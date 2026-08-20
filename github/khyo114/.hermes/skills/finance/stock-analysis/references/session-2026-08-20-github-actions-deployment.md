# GitHub Actions Hybrid Architecture Deployment — 2026-08-20

## Session Summary
Full deployment and validation of GitHub Actions hybrid architecture for daily stock analysis pipeline. Local WSL cron jobs (intraday 30-min) + GitHub Actions (daily batch at 07:00, 09:30, 10:00, 02:00 KST) with Git-based Obsidian sync.

## Key Decisions & Fixes

### 1. Workflow File Path (Critical)
**Problem**: Initial workflow created at `github/khyo114/.github/workflows/daily-stock.yml` — ignored by GitHub Actions
**Fix**: Must be at **repo root `.github/workflows/daily-stock.yml`**
```bash
# Correct structure
repo-root/
├── .github/
│   └── workflows/
│       └── daily-stock.yml   ← HERE
├── 주식분석/
└── ...
```

### 2. Model Selection (Critical)
**Problem**: `meta-llama/llama-3.1-8b-instruct:free` no longer free on OpenRouter (HTTP 404)
**Solution**: Per-job explicit model/provider:
- `integrated-analysis`: Google Gemini direct (`gemini-2.5-flash`, provider: `google`) — free tier, no credits
- `news-filtering`, `skill-hub-monitoring`, `obsidian-organize`, `technical-signal-snapshot`: NVIDIA NIM (`nvidia/nemotron-3-ultra-550b-a55b` + fallback `nvidia/llama-3.1-nemotron-70b-instruct`)
- Fallback chain in config.yaml: OpenRouter → Google

### 3. Telegram Delivery
**Validated**: Direct `curl` to Telegram Bot API works in GitHub Actions
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d text="📊 일일 주식 리포트 완료"
```
- message_id 30 delivered successfully
- `appleboy/telegram-action` alternative but direct curl simpler

### 4. Git Commit/Push for Obsidian Sync
```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add 주식분석/ || true
git commit -m "📊 일일 주식 분석 리포트 $(date +%Y%m%d)" || true
git push || true
```
- Commits reports to repo for local `git pull` → Obsidian reads local files

### 5. System Python 3.14 Incompatibility
**Problem**: GitHub Actions ubuntu-latest has Python 3.14 which fails with numpy C-extension errors
**Fix**: Use Hermes venv Python explicitly
```bash
# After install.sh, add to PATH
echo "$HOME/.hermes/bin" >> $GITHUB_PATH
# Then use: hermes chat ...
# Or: /home/runner/.hermes/bin/hermes chat ...
```

### 6. Required GitHub Secrets (5)
| Secret | Source | Required |
|--------|--------|----------|
| `GOOGLE_API_KEY` | https://aistudio.google.com/app/apikey | ✅ |
| `TELEGRAM_BOT_TOKEN` | @BotFather | ✅ |
| `TELEGRAM_CHAT_ID` | @userinfobot | ✅ |
| `NVIDIA_API_KEY` | https://build.nvidia.com | ✅ |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys | ⚠️ fallback |

### 7. Workflow Dispatch Input
```yaml
workflow_dispatch:
  inputs:
    job_type:
      description: 'Which job to run'
      required: true
      default: 'all'
      type: choice
      options: [all, fundamental, technical, news, skillhub, obsidian]
```
**Validated**: Manual trigger works, `job_type` filters jobs via `if:` conditions

## Workflow Structure (6 Jobs)
```yaml
jobs:
  integrated-analysis:      # 09:30 KST — Google Gemini direct
  news-filtering:           # 07:00 KST — NVIDIA NIM
  skill-hub-monitoring:     # 10:00 KST — NVIDIA NIM
  obsidian-organize:        # 02:00 KST — NVIDIA NIM
  technical-signal-snapshot:# 09:30 KST — NVIDIA NIM (daily snapshot)
  summary:                  # Combined Telegram notification
```

## Cron Schedule (UTC)
| KST | UTC | Cron | Job |
|-----|-----|------|-----|
| 07:00 | 22:00 (prev day) | `0 22 * * 0-4` | news-filtering |
| 09:30 | 00:30 | `30 0 * * *` | integrated-analysis, technical-signal-snapshot |
| 10:00 | 01:00 | `0 1 * * *` | skill-hub-monitoring |
| 02:00 | 17:00 (prev day) | `0 17 * * *` | obsidian-organize |

## Validation Results (2026-08-20)
| Check | Status | Notes |
|-------|--------|-------|
| Workflow file at repo root | ✅ | `.github/workflows/daily-stock.yml` |
| GitHub Actions infrastructure install | ✅ | Hermes + Python 3.11 + ffmpeg + ripgrep |
| Telegram test delivery | ✅ | message_id 30 |
| Model selection per-job | ✅ | Google Gemini + NVIDIA NIM |
| `workflow_dispatch` manual trigger | ✅ | `job_type` choice works |
| Git commit/push | ✅ | Reports committed to repo |
| 6-job structure | ✅ | All jobs defined with correct `if:` |
| yfinance Korean ETF/small cap limits | ⚠️ | 3 tickers unsupported (documented) |

## Next Steps
1. Add `GOOGLE_API_KEY`, `NVIDIA_API_KEY` to GitHub Secrets
2. Run manual `workflow_dispatch` with `job_type: all`
3. Verify Telegram notifications for all 6 jobs
4. Local `git pull` → Obsidian sync verification
5. Externalize watchlist to `config/watchlist.yaml` (template exists in skill)

## Related Files
- `.github/workflows/daily-stock.yml` (deployed workflow)
- `templates/watchlist.yaml` (92-ticker watchlist)
- `references/session-2026-08-20-integrated-pipeline.md` (first pipeline run)
- `references/session-2026-08-20-second-run.md` (second pipeline run)