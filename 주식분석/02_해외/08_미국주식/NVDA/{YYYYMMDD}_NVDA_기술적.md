# NVDA(엔비디아) 기술적 시그널 - {YYYYMMDD}

**태그**: #기술적분석 #볼린저밴드 #쌍굴파기 #시그널 #NVDA

## 시그널 정보

- **시그널**: **매수 신호** (BREAKOUT 확인)
- **단계**: BREAKOUT (6단계 중 5단계 - 넥라인 돌파 확인)
- **날짜**: {YYYYMMDD} 현재가 기준
- **현재가**: ${current_price:,.0f}원

## 패턴 상세

### 1차 바닥 (첫 저점)
- 가격: ${first_bottom_price:,.0f}원
- 날짜: {first_bottom_date}
- 상태: 하단 2σ 밴드(Touch) 후 반등 확인

### 넥라인 (중간 고점)
- 가격: ${neckline_price:,.0f}원
- 형성 일자: {neckline_date}
- 확인: 중간 반등 후 저항선 역할

### 2차 바닥 (두 저점)
- 가격: ${second_bottom_price:,.0f}원
- 날짜: {second_bottom_date}
- 상태: Higher Low 형성 (첫 저점보다 높음)
- 확인: 하단 1σ 밴드 근접 지지

## 거래 조건

| 항목 | 가격 | 비고 |
|------|------|------|
| **진입가** | ${entry_price:,.0f}원 | 넥라인 상향 돌파 종가 기준 매수 |
| **손절가** | ${stop_price:,.0f}원 | 2차 바닥 저점 하향 이탈 시 손절 |
| **목표가** | ${target_price:,.0f}원 | 넥라인 + (넥라인 - 2차 바닥) 측정치 프로젝션 |

## 리스크 분석

- **리스크 레벨**: MEDIUM
- **R:R 비율**: {(target_price - entry_price) / (entry_price - stop_price):.2f}
- 손절가 이하로 하락 시 원금 손실 위험
- 목표가 이상 달성은 시장 흐름에 따라 변동 가능

## LLM 요약 (Telegram 3줄)

> **종목: NVDA**(현재가 ${current_price:,.0f})
> 
> **시그널: 매수 신호** / 단계: BREAKOUT
> 
> **진입가 ${entry_price:,.0f} | 손절 ${stop_price:,.0f} | 목표 ${target_price:,.0f}** / 리스크: MEDIUM

## 패턴 타임라인

```
{first_bottom_date}      {neckline_date}      {second_bottom_date}      {signal_date}
    ↘              ↘              ↘              ↘
     1차 바닥 → 넥라인 돌파 → 2차 바닥 → 매수 시그널
```

## 주의사항

- **손절 실행**: 진입일로부터 60분 이내 손절가 하향 이탈 시 즉시 청산 권장
- **익절 전략**: 목표가 달성 또는 1σ 밴드 하향 이탈 시 부분 익절 고려
- **시장 상황**: 전체 시장 지수 동반 하락 시 개별 종목 손절 확률 상승
- **데이터 제한**: 30분봉 기반 진단이며, 일봉/주봉 추세와도 확인 권장
- **중복 신호 억제**: 동일 종목에서 60분 이내 중복 시그널은 억제됨