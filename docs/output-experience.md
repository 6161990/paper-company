# Output Experience

Paper Company의 결과물은 링크 목록이 아니다.

목표는 `읽는 순간 흥미가 생기고, 오늘 뭔가 해보고 싶어지는 콘텐츠`다.

## Core Output

매일 아침 기본 결과물은 `Morning Signal`이다.

```text
Paper Company - Morning Signal
2026-05-10

오늘의 분위기:
AI agent가 단순 코딩 보조를 넘어 운영 자동화 쪽으로 움직이고 있음.
특히 incident triage와 observability 쪽이 네 백엔드 관심사와 강하게 맞물림.

오늘의 TOP 5:
1. Claude Agent SDK로 incident triage agent 만들기
2. GitHub Trending에서 발견한 queue observability tool
3. 혼자 쓰는 자동화 SaaS 아이디어
4. 미래 신호를 수집하는 인물 설정
5. 영감 주는 개발자의 작업 방식
```

## Item Card

각 아이템은 Paperclip에서 카드로 보여준다.

```text
Title:
Claude Agent SDK로 incident triage agent 만들기

Hook:
이건 네가 좋아하는 "살아 움직이는 백엔드 관제실"과 거의 바로 연결된다.

Why it matters:
장애 로그를 사람이 보는 대신 Agent가 먼저 분류하고, 원인 후보와 다음 행동을 제안하는 흐름이다.

Why you may like it:
n8n, Claude Agent SDK, backend 장애 분석, Paperclip UI가 한 번에 연결된다.

30-minute move:
가짜 장애 로그 5개를 만들고, Claude가 severity와 next action을 분류하게 해본다.

Content angle:
"AI가 백엔드 장애를 먼저 읽어주는 시대"라는 블로그 글로 확장 가능.

Feedback:
[Save] [Like] [Dislike] [Acted] [More like this]
```

## Output Modes

### 1. Morning Signal

매일 아침 받는 짧은 브리프.

목적:

- 오늘의 자극 제공
- TOP 5 확인
- Paperclip으로 들어오게 만들기

전송 채널:

- Telegram
- email
- Slack

### 2. Paperclip Cards

Paperclip UI에서 보는 상세 카드.

목적:

- 추천 이유 확인
- Agent reasoning 확인
- 피드백 입력
- 다시 랭킹 요청

### 3. Deep Dive

마음에 드는 아이템을 클릭했을 때 나오는 확장 콘텐츠.

포함:

- 원본 링크
- 관련 링크
- 왜 이 방향으로 탐색이 이어졌는지
- 3단계 실행 계획
- 블로그/영상/프로젝트 angle

### 4. Action Prompt

바로 움직이게 하는 30분짜리 행동.

예:

```text
오늘 30분:
가짜 장애 로그 5개를 `data/sample_incidents.json`에 만든다.
Claude Agent SDK가 severity, suspected cause, next action을 뽑게 한다.
```

### 5. Weekly Pattern

매주 한 번, 내가 어떤 것에 반응했는지 정리한다.

예:

```text
이번 주 너를 움직인 패턴:
- 추상적인 AI 뉴스보다 실제 agent workflow에 반응함
- backend + automation 조합에서 행동률이 높음
- 소설 아이디어는 밤 시간대에 더 반응함
```

## Tone

Paper Company의 출력은 다음 느낌이어야 한다.

- 건조한 뉴스 요약이 아니다.
- 과장된 자기계발 문구가 아니다.
- 친구가 던져주는 링크도 아니다.
- 내 취향을 아는 사내 리서처가 아침에 올리는 brief다.

좋은 문장:

```text
이건 네 Paperclip 관제실과 바로 연결된다.
```

별로인 문장:

```text
이 글은 AI 산업의 미래를 이해하는 데 중요합니다.
```

## Quality Bar

좋은 결과물의 기준:

- 제목만 봐도 클릭하고 싶다.
- 왜 나에게 맞는지 구체적이다.
- 오늘 할 행동이 작고 명확하다.
- 콘텐츠/프로젝트로 확장할 수 있다.
- 피드백 버튼을 누르고 싶어진다.

나쁜 결과물:

- 링크만 모아둔 것
- 일반적인 뉴스 요약
- 너무 거대한 계획
- 오늘 할 행동이 없는 아이템
- 내 취향과 연결 설명이 약한 추천
