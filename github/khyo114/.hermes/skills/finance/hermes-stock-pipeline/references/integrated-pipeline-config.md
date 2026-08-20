# 통합 파이프라인 크론 설정 (2026-08-17 세션)

## 생성된 크론 잡
- **Job ID**: `abb99fffa684`
- **이름**: `통합 주식분석 파이프라인 (펀더멘털 + 기술적)`
- **스케줄**: `30 9 * * *` (매일 09:30 KST)
- **스킬**: `stock-analysis`, `technical-trading`, `hermes-stock-pipeline`
- **모델**: `google/gemini-2.5-flash-lite` (provider: `openrouter`)
- **전달**: `origin,telegram:6723387878`

## 프롬프트 요약
```
1단계: 펀더멘털 분석 (stock-analysis)
- 대상 10종목: 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790), NVDY, NVDA, QQQ, (나머지 2개 기존 유지)
- 뉴스·공시·유튜브·전문가 의견·재무제표·계약 수집
- 저장: 주식분석/{종목명}/{YYYYMMDD}_{종목명}.md + 통합 리포트

2단계: 기술적 분석 (technical-trading)
- 핵심 5종목: 삼성전자(005930), NVDA, 우리로(046970), SKC(011790), TIGER K방산&우주(453830)
- 쌍굴파기 이중 볼린저밴드 백테스트 + 현재 시그널 진단
- yfinance로 3년 일봉 수집 (브라우저 미사용)
- 저장: 주식분석/{종목명}/{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md

3단계: Telegram 통합 알림
- 펀더멘털 요약 + 기술적 요약 + 저장 경로 + 실행 시간/에러
```

## 실행 원칙 (이 세션에서 확립)
- web_search/web_extract만 사용 (브라우저 자동화 금지)
- yfinance로 가격 데이터 수집 (FinanceDataReader 미작동 환경)
- Windows 경로는 포워드 슬래시(/) 또는 raw string 사용
- 인코딩: UTF-8 강제 (LANG=ko_KR.UTF-8, PYTHONIOENCODING=utf-8)
- 에러 발생 시 해당 종목만 스킵하고 계속 진행

## Telegram 게이트웨이 설정 (필수)
```bash
hermes gateway setup   # Telegram 선택 → 토큰/챗ID 입력
hermes gateway install && hermes gateway start
# systemd linger 활성화 필요 (WSL에서 로그아웃 후 생존)
```

## 중복 크론 정리
- 기존 단일 분석 잡(`e70a7a1f1729`)은 **paused** 처리
- 통합 파이프라인(`abb99fffa684`)만 활성