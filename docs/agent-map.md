# Agent Map

Paper Company는 여러 관심사 에이전트가 한 회사의 팀처럼 움직이는 구조로 간다.

중요한 점:

로컬 MVP에서 실제 프로세스는 하나만 실행한다.

```text
one Claude Agent SDK run
  -> internally acts as multiple interest agents
  -> merges findings
  -> curates Morning Signal TOP 5
```

즉, 지금 당장 여러 서버나 여러 프로세스를 띄우는 것이 아니다. 하나의 Claude Agent SDK 실행 안에서 여러 관점으로 탐색하게 만든다.

## Interest Agents

### AI Agent

찾는 것:

- Claude Agent SDK 사례
- AI agent workflow
- AI startup
- 개발자가 바로 따라 해볼 수 있는 AI 자동화

추천 기준:

- Paper Company에 바로 붙일 수 있는가
- “이거 만들어보고 싶다”는 느낌이 오는가
- n8n, Paperclip, backend 시스템과 연결되는가

### Backend Agent

찾는 것:

- 장애 분석 글
- 데이터 파이프라인
- retry, queue, observability, infra
- GitHub Trending backend repo
- LINE/LY Corporation Tech Blog
- 우아한형제들 기술블로그
- Google Developers Blog
- NAVER D2

추천 기준:

- 실무 감각을 키우는가
- 나중에 블로그 글감이 되는가
- 자동화/관제실 아이디어로 연결되는가
- 한국 백엔드 개발자 관점에서 적용 가능한가

### Money Agent

찾는 것:

- 오늘의 주식/시장 소식
- 기업과 산업 흐름
- ERP, 회계, 재무제표, 비즈니스 운영 개념
- 하루에 하나씩 이해할 수 있는 돈/회사 개념

추천 기준:

- 실제 시장 소식과 연결되는가
- 하루에 하나씩 개념을 쌓을 수 있는가
- 백엔드 개발자가 회사/비즈니스를 이해하는 데 도움이 되는가
- Paper Company 운영 감각에 도움이 되는가

### Inspiring People Agent

찾는 것:

- 영감 주는 창업자/개발자/크리에이터
- 일하는 방식
- 루틴, 철학, 프로젝트 운영법

추천 기준:

- 따라 해보고 싶은 행동이 있는가
- 지금의 Paper Company 운영 방식에 힌트를 주는가
- 단순 명언이 아니라 실제 작업 방식으로 연결되는가

## Curation Agent

역할:

- 각 관심사 에이전트 관점의 발견을 합친다.
- 중복과 저품질 발견을 제거한다.
- `ubuntu src가 오늘 꽂힐 확률` 기준으로 TOP 5를 고른다.
- 한 분야로 너무 쏠리면 균형을 조정한다.

판단 기준:

- Momentum: 지금 당장 해보고 싶은가
- Fit: 내 관심사와 맞는가
- Leverage: 프로젝트/콘텐츠/학습으로 확장되는가
- Novelty: 새롭거나 시야를 넓히는가
- Reality: 오늘 30분 안에 첫 행동이 가능한가

## Later Runtime Split

나중에 필요해지면 실제 실행 단위도 나눌 수 있다.

예:

```text
AI Agent process
Backend Agent process
Money Agent process
Inspiring People Agent process
```

하지만 초기에는 하나의 Claude Agent SDK 실행 안에서 역할만 나눠도 충분하다.
