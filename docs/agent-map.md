# Agent Map

로컬 MVP에서는 에이전트를 하나만 둔다.

여러 에이전트로 나누면 관제실은 멋있어 보이지만, 지금 단계에서는 프롬프트 관리, 로그 관리, 피드백 반영이 불필요하게 복잡해진다.

## Local MVP Agent

### Paper Company Exploration Agent

역할:

- 오늘의 관심사와 최근 피드백을 읽는다.
- 웹과 공개 소스를 탐색한다.
- 좋은 방향이 보이면 더 깊게 파고든다.
- 별로면 다른 방향으로 전환한다.
- 발견한 아이템을 네 취향 기준으로 큐레이션한다.
- Paperclip에서 피드백받기 좋은 형태로 TOP 5를 만든다.

탐색 범위:

- AI learning
- Claude Agent SDK
- backend engineering
- money-making automation
- inspiring people
- fiction ideas

판단 기준:

- Momentum: 지금 당장 해보고 싶은가
- Fit: 내 관심사와 맞는가
- Leverage: 프로젝트/콘텐츠/학습으로 확장되는가
- Novelty: 새롭거나 시야를 넓히는가
- Reality: 오늘 30분 안에 첫 행동이 가능한가

## Later Expansion

나중에 필요해지면 에이전트를 나눌 수 있다.

예:

- AI/Agent Research
- Backend Systems
- Money Automation
- Fiction/Story

하지만 이건 Paperclip 피드백 데이터가 쌓인 뒤에 판단한다.

초기 원칙:

```text
one agent first
split only when the feedback says we need it
```
