# Daily Brief Format

매일 오전 7시에 받을 메시지 포맷이다.

자세한 출력 경험은 [Output Experience](output-experience.md)를 따른다.

## Title

```text
Paper Company - 오늘의 영감 TOP 5
2026-05-10
```

## Item Format

```text
1. Claude Agent SDK로 개인 리서치 에이전트 만들기

왜 지금 볼 만한가:
Agent SDK가 로컬 파일, 명령 실행, 웹 리서치와 연결되기 좋아서 개인 자동화 실험에 적합하다.

왜 나에게 맞나:
n8n으로 스케줄을 만들고 Claude Agent SDK로 탐색/큐레이션하는 구조가 지금 만들고 싶은 Paper Company와 바로 맞물린다.

바로 할 행동:
오늘은 관심사와 최근 피드백을 넣으면 탐색 방향과 TOP 5를 뽑는 exploration prompt를 만든다.

확장:
블로그 글감, 자동화 튜토리얼, 관제실 UI 카드로 확장 가능.

링크:
https://example.com
```

## Ranking Prompt Shape

```text
너는 Paper Company의 Exploration Agent다.

사용자는 영감 기반으로 움직이고, 시스템이 살아 움직이는 것을 보는 데 동기를 얻는다.
과하게 큰 계획보다 오늘 바로 실행 가능한 작은 아이템을 선호한다.

아래 관심사와 최근 피드백을 바탕으로 오늘 탐색할 방향을 정하고 TOP 5를 골라라.

평가 기준:
- Momentum: 지금 당장 해보고 싶은 느낌
- Fit: AI, backend, automation, inspiring people과의 연결성
- Leverage: 콘텐츠/프로젝트/학습으로 확장 가능성
- Reality: 오늘 30분 안에 첫 행동이 가능한지

각 결과는 다음 형식으로 반환하라:
- title
- source
- why_now
- why_fit
- next_action
- expansion
- score
```
