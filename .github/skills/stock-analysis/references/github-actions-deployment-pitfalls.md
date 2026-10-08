# GitHub Actions Deployment Pitfalls — Lessons Learned (2026-08-20)

## Critical Issues Encountered

### 1. Workflow File Location (MUST be at repo root)

**Problem**: Workflow at `github/khyo114/.github/workflows/daily-stock.yml` was ignored by GitHub Actions.

**Root Cause**: GitHub Actions only scans `.github/workflows/` at the **repository root**.

**Solution**: 
```bash
# Check repo root
git rev-parse --show-toplevel
# Must show: /home/runner/work/khyo114/khyo114 (or equivalent)

# Workflow must be at:
<repo-root>/.github/workflows/daily-stock.yml
```

**Verification**: `git ls-tree -r HEAD --name-only | grep workflow` should show `.github/workflows/daily-stock.yml`

---

### 2. Free Model Deprecation on OpenRouter

**Problem**: `meta-llama/llama-3.1-8b-instruct:free` returns HTTP 404: "This model is unavailable for free."

**Root Cause**: OpenRouter periodically removes free tiers for older models.

**Solution**: Use working free alternatives:
- **Google Gemini direct**: `gemini-2.5-flash` via Google provider (no credits needed)
- **NVIDIA NIM**: `nvidia/nemotron-3-ultra-550b-a55b` with `NVIDIA_API_KEY` (monthly free credits)
- **Fallback chain**: Explicit per-job model config

```yaml
# In workflow - Google Gemini (free, no API credits consumed)
- name: Configure Hermes
  run: |
    hermes config set model.default gemini-2.5-flash
    hermes config set model.provider google
```

---

### 3. System Python Version Incompatibility

**Problem**: GitHub runner system Python 3.14 breaks numpy/pandas installation.

**Error**: `ERROR: Cannot install numpy because Python 3.14 is not supported`

**Solution**: Explicitly install Python 3.11:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
```

---

### 4. workflow_dispatch Input Definition Required

**Problem**: Manual trigger (`Run workflow` button) shows no input dropdown.

**Root Cause**: `workflow_dispatch.inputs` not defined in workflow YAML.

**Solution**: Define inputs for selective job execution:
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

**Job condition**: `if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'fundamental'`

---

### 5. Git-based Obsidian Sync Pattern

**Problem**: GitHub Actions cannot write to local Obsidian vault.

**Solution**: 
1. Actions commits reports to repo (`주식분석/` folder)
2. Local machine runs `git pull` to sync
3. Obsidian reads local vault

```yaml
- name: Commit & Push Reports
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add 주식분석/ || true
    git commit -m "📊 일일 주식 분석 리포트 $(date +%Y%m%d)" || true
    git push || true
```

---

### 6. Windows/WSL Repo Root Confusion

**Problem**: `C:/Users/kho/github/khyo114` is NOT the git repo root.

**Discovery**: `git rev-parse --show-toplevel` → `C:/Users/kho`

**Impact**: Workflow file placed in wrong location, git operations fail.

**Fix**: Always verify repo root before adding workflows:
```bash
cd $(git rev-parse --show-toplevel)
mkdir -p .github/workflows
# Place workflow here
```

---

### 7. Telegram Bot Token/Chat ID in Secrets

**Required GitHub Secrets**:
| Secret | Source |
|--------|--------|
| `GOOGLE_API_KEY` | https://aistudio.google.com/apikey |
| `TELEGRAM_BOT_TOKEN` | @BotFather |
| `TELEGRAM_CHAT_ID` | Numeric (e.g., 6723387878) |
| `NVIDIA_API_KEY` | https://build.nvidia.com |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys (optional fallback) |

**Telegram test in workflow**:
```yaml
- name: Test Telegram
  run: |
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id=${TELEGRAM_CHAT_ID} \
      -d text="📊 테스트 메시지"
```

---

### 8. Model Selection Per-Job (Explicit)

**Pattern**: Different jobs need different models for cost/performance:
```yaml
# Fundamental analysis - Google Gemini (free, fast)
- name: Configure Hermes
  run: |
    hermes config set model.default gemini-2.5-flash
    hermes config set model.provider google

# Technical/News/Skillhub - NVIDIA NIM (550B primary, 70B fallback)
- name: Configure Hermes
  run: |
    hermes config set model.default nvidia/nemotron-3-ultra-550b-a55b
    hermes config set model.provider nvidia
    hermes config set fallback.model nvidia/llama-3.1-nemotron-70b-instruct
    hermes config set fallback.provider nvidia
```

---

### 9. Multi-Job Workflow with Summary

**Structure**: 5 parallel jobs + 1 summary job
```yaml
jobs:
  integrated-analysis:     # 09:30 KST
  news-filtering:          # 07:00 KST
  skill-hub-monitoring:    # 10:00 KST
  obsidian-organize:       # 02:00 KST
  technical-signal-snapshot: # 09:30 KST (once daily)
  summary:
    needs: [all 5 jobs]
    if: always()
```

---

## Quick Validation Checklist

Before deploying workflow:
- [ ] Workflow at `.github/workflows/` (repo root)
- [ ] `workflow_dispatch.inputs` defined
- [ ] Python 3.11 explicitly in `setup-python`
- [ ] Working free model configured per job
- [ ] All 5 GitHub Secrets added
- [ ] Telegram test succeeds
- [ ] `git push` from workflow works (permissions)
- [ ] Local `git pull` syncs to Obsidian

---

## Hybrid Architecture Summary

| Layer | Schedule | Environment | Purpose |
|-------|----------|-------------|---------|
| **GitHub Actions** | 07:00, 09:30, 10:00, 02:00 KST | Cloud (always on) | Daily batch: fundamental, news, skillhub, obsidian |
| **Local WSL Cron** | 09:00-15:30 every 30min (weekdays) | Local (PC must be on) | Intraday technical signals |
| **Obsidian Sync** | After Actions runs | Manual/local cron | `git pull` → view in Obsidian |

**Key principle**: GitHub Actions for reliability (runs when PC off), Local cron for frequency (sub-hour not reliable in Actions).