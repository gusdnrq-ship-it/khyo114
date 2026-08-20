# Hermes 크론 잡 모델 핀 고정 가이드
# Configuration Drift 에러 방지 및 해결

## 문제: Configuration Drift 에러

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created 
(provider 'nvidia' -> 'gemini'; model 'nvidia/nemotron-3-ultra-550b-a55b' -> 'gemini-2.5-flash'), 
and this job is unpinned. No inference call was made. 
To run on the new config, pin it explicitly: 
`cronjob action=update job_id=<job_id> provider=<provider> model=<model>` 
(or pin the original values to keep them). See #44585.
```

## 원인

크론 잡 생성 시점의 `provider_snapshot` / `model_snapshot`과 현재 전역 설정(`config.yaml`의 `model.default`, `model.provider`)이 다를 때, 잡이 **unpinned** 상태면 실행 차단됨.

## 해결 방법 3가지

### 방법 1: cronjob 툴로 명시적 업데이트 (권장)

```bash
# 현재 모델/프로바이더로 핀 고정
cronjob action=update job_id=e70a7a1f1729 provider=google model=gemini-2.5-flash

# OpenRouter 사용하는 경우
cronjob action=update job_id=e70a7a1f1729 provider=openrouter model=google/gemma-2-9b-it:free
```

> **중요**: CLI 명령어 `hermes cron edit`은 현재 `--model/--provider` 플래그를 지원하지 않습니다. 내부 `cronjob` 툴(`action='update'`, `model` 파라미터)을 사용해야 합니다.

### 방법 2: jobs.json 직접 수정

```bash
# 파일 열기
cat ~/.hermes/cron/jobs.json

# 해당 잡의 model/provider 필드 채우기 (null → 실제 값)
{
  "model": "gemini-2.5-flash",
  "provider": "google",
  "provider_snapshot": "nvidia",
  "model_snapshot": "nvidia/nemotron-3-ultra-550b-a55b"
}
```

### 방법 3: 크론 잡 생성 시 명시적 지정

```bash
hermes cron create "30 9 * * *" "프롬프트" \
  --skill stock-analysis \
  --model google/gemini-2.5-flash \
  --provider google \
  --name "일일 주식분석 리포트"
```

## 예방: config.yaml에 크론 전용 모델 설정

```yaml
cron:
  model: google/gemini-2.5-flash
  model_provider: google
```

이렇게 하면 새로 생성되는 크론 잡은 기본적으로 이 모델을 사용함.

## 확인 방법

```bash
# 크론 잡 목록 및 상태 확인
hermes cron list

# 특정 잡 상세 확인
hermes cron status
```

## 이 세션에서 발생한 사례

| 잡 ID | 생성 시 모델 | 현재 모델 | 결과 |
|-------|-------------|-----------|------|
| e70a7a1f1729 | NVIDIA | Google Gemini | Drift 에러로 실패 |
| 96aa87e21ec6 | OpenRouter (키 없음) | - | 생성 후 즉시 실패 |

**해결**: `cronjob action=update job_id=e70a7a1f1729 provider=google model=gemini-2.5-flash` 실행 후 정상 작동

---

## OpenRouter 무료 티어 한도 (HTTP 402 에러)

OpenRouter로 전환 후에도 무료 크레딧 한도에 걸릴 수 있습니다:

```
RuntimeError: HTTP 402: This request requires more credits, or fewer max_tokens. You requested up to 65535 tokens, but can only afford 16000. To increase, visit https://openrouter.ai/settings/credits and upgrade to a paid account
```

**원인**: OpenRouter 무료 티어도 일일 크레딧/토큰 한도가 있습니다.

**대응 전략**:
1. **더 저렴한 무료 모델 사용** — `google/gemini-2.5-flash-lite`, `deepseek/deepseek-chat`, 또는 `:free` 접미사 모델
2. **Google Gemini로 복귀** — UTC 자정에 일일 한도 리셋되면 다시 사용 가능
3. **프롬프트/출력 길이 줄이기** — max_tokens 제한이 걸리는 경우
4. **크레딧 충전** — 유료 계정 전환

**모델 추천 (무료 티어 친화적)**:
| 모델 | 특징 |
|------|------|
| `google/gemini-2.5-flash-lite` | 매우 저렴, 요약용 적합 |
| `deepseek/deepseek-chat` | 무료 티어 넉넉함 |
| `meta-llama/llama-3.1-8b-instruct:free` | OpenRouter 무료 티어 |
| `microsoft/phi-3-mini-128k-instruct:free` | 긴 컨텍스트, 무료 |