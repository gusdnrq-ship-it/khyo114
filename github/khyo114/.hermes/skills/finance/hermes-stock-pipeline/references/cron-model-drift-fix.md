# Cron Job Model Drift Fix

## Problem

When Hermes config changes (model/provider), existing cron jobs fail with:

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'nvidia' -> 'gemini'; model 'nvidia/nemotron-3-ultra-550b-a55b' -> 'gemini-2.5-flash'), and this job is unpinned. No inference call was made. To run on the new config, pin it explicitly: `cronjob action=update job_id=... provider=<provider> model=<model>` (or pin the original values to keep them). See #44585.
```

## Root Cause

Cron jobs store `provider_snapshot` and `model_snapshot` at creation time. When global config changes, Hermes refuses to run with drifted config unless explicitly pinned.

## Solutions

### Option 1: Edit jobs.json directly (immediate fix)

File: `~/.hermes/cron/jobs.json`

Find the job and set `model` and `provider` fields:

```json
{
  "id": "e70a7a1f1729",
  "model": "gemini-2.5-flash",
  "provider": "google",
  "provider_snapshot": "nvidia",
  "model_snapshot": "nvidia/nemotron-3-ultra-550b-a55b",
  ...
}
```

### Option 2: Recreate cron job with explicit model

```bash
# Delete old job
hermes cron remove <job_id>

# Create new with explicit model
hermes cron create "30 9 * * *" \
  "stock-analysis 스킬로 10종목 분석 후 옵시디언 저장" \
  --skill stock-analysis \
  --name "일일 주식분석 리포트 (10종목)" \
  --model google/gemini-2.5-flash \
  --provider google \
  --deliver origin
```

### Option 3: Update existing job (if hermes cron edit supports it)

```bash
hermes cron edit <job_id> --model google/gemini-2.5-flash --provider google
```

## Prevention

Always specify model/provider when creating cron jobs:

```yaml
# In config.yaml
cron:
  model: google/gemini-2.5-flash
  model_provider: google
```

And when creating via CLI:
```bash
hermes cron create "30 9 * * *" "prompt" --skill stock-analysis --model google/gemini-2.5-flash --provider google
```

## Verification

After fix, test run:
```bash
hermes cron run <job_id>
```

Should execute without "config drifted" error.