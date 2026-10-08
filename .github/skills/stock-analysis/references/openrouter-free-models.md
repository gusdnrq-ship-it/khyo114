# OpenRouter 무료 모델 현황 및 선택 가이드
# 2024-08 기준 검증된 모델들

## 현재 작동하는 무료 모델 (OpenRouter)

| 모델 ID | 제공사 | 컨텍스트 | 비고 |
|---------|--------|----------|------|
| `google/gemma-2-9b-it:free` | Google | 8k | ✅ **추천** - 안정적 작동 확인 |
| `google/gemma-7b-it:free` | Google | 8k | ✅ 대안 |
| `microsoft/phi-3-mini-128k-instruct:free` | Microsoft | 128k | ✅ 대안 (긴 컨텍스트) |

## 더 이상 무료가 아닌 모델

| 모델 ID | 상태 |
|---------|------|
| `meta-llama/llama-3.1-8b-instruct:free` | ❌ 유료 전환됨 (2024-08) |
| `meta-llama/llama-3-8b-instruct:free` | ❌ 유료 전환됨 |

## 모델 설정 명령어

```bash
# 추천: gemma-2-9b-it:free
hermes config set model.default google/gemma-2-9b-it:free
hermes config set model.provider openrouter
hermes config set model.base_url https://openrouter.ai/api/v1

# 대안: phi-3-mini-128k (긴 컨텍스트 필요 시)
hermes config set model.default microsoft/phi-3-mini-128k-instruct:free
hermes config set model.provider openrouter
hermes config set model.base_url https://openrouter.ai/api/v1
```

## GitHub Actions에서 사용 시

```yaml
- name: Configure Hermes Model
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: |
    hermes config set model.default google/gemma-2-9b-it:free
    hermes config set model.provider openrouter
    hermes config set model.base_url https://openrouter.ai/api/v1
```

## 주의사항

1. **Google Gemini 무료 티어**는 하루 20회 한도 → Hermes 세션 1회에도 부족
2. **OpenRouter 무료 티어**는 일일 수백 회 가능 → Hermes 자동화에 적합
3. 모델명 뒤에 `:free` 접미사 필수 (유료 버전과 구분)
4. OpenRouter 크레딧 소진 시 402 에러 → 크레딧 충전 또는 다른 무료 모델로 전환

## OpenRouter 크레딧 확인
- https://openrouter.ai/settings/credits
- 무료 티어라도 가입 시 소량 크레딧 지급됨