# Paper Company Roadmap

Paper Company는 `매일 아침 나에게 맞는 영감 아이템 TOP 5를 자동으로 받는 시스템`이다.

도구는 세 가지 역할로 나눈다.

```text
n8n
  -> 매일 정해진 시간에 탐색 에이전트를 깨우고, 결과를 전송한다.

Claude Agent SDK
  -> 매일 나 대신 세상을 탐색하고, 좋은 방향을 더 파고들고, 내 취향에 맞는 TOP 5를 만든다.

Paperclip UI
  -> 오늘 무엇이 돌았는지, 무엇을 찾았는지, 왜 추천했는지, 어디서 실패했는지 보여준다.

Telegram Bot
  -> 모바일에서 Paper Company에게 실시간으로 일을 시키는 명령창이다.
```

상세 실행 구조는 [Runtime Plan](runtime-plan.md)을 따른다.
피드백 구조는 [Feedback Loop](feedback-loop.md)을 따른다.
출력 경험은 [Output Experience](output-experience.md)를 따른다.
모바일 명령창은 [Telegram Interface](telegram-interface.md)를 따른다.

## Where The 7 AM Trigger Runs

매일 오전 7시 실행은 반드시 어딘가에서 계속 켜져 있어야 한다.

로컬 노트북의 n8n은 학습과 실험용으로 좋지만, 노트북이 꺼져 있으면 오전 7시에 실행되지 않는다. 그래서 운영 방식은 단계별로 나눈다.

### Option A: Local n8n

용도:

- 지금 배우기
- 워크플로우 만들기
- 버튼 눌러 수동 실행 테스트

장점:

- 무료
- 바로 수정 가능
- 구조를 이해하기 좋음

단점:

- 노트북이 꺼져 있으면 7시 실행 안 됨
- Docker Desktop이 켜져 있어야 함

### Option B: Small VPS

용도:

- 실제 매일 오전 7시 자동 실행
- Telegram 전송
- Paperclip UI 상시 접속

후보:

- Hetzner
- DigitalOcean
- AWS Lightsail
- Oracle Cloud Free Tier
- Render/Fly.io/Railway 같은 PaaS

장점:

- 서버가 24시간 켜져 있음
- n8n Schedule Trigger가 안정적으로 돈다
- 나중에 Paperclip UI도 같은 서버에 올릴 수 있음

단점:

- 서버 비용 또는 설정 관리가 필요함
- API 키와 보안 설정을 챙겨야 함

### Option C: n8n Cloud

용도:

- 서버 관리 없이 n8n만 쓰기

장점:

- 가장 편함
- 스케줄 실행이 안정적

단점:

- 비용이 있음
- 로컬 Python/Claude Agent SDK 스크립트 실행이 제한적일 수 있음
- Paperclip UI와 SQLite를 따로 운영해야 할 가능성이 큼

## Recommended Hosting Plan

이 프로젝트에는 `Option B: Small VPS`가 가장 맞다.

이유:

- n8n이 매일 7시에 안정적으로 돌아야 한다.
- Claude Agent SDK 스크립트를 같은 서버에서 실행할 수 있다.
- SQLite를 같은 서버에 둘 수 있다.
- Paperclip UI도 같은 서버에 붙일 수 있다.

초기 운영 구조:

```text
Small VPS
  |
  +-- Docker Compose
        |
        +-- n8n container
        +-- Paperclip UI container
        +-- SQLite file volume
        +-- scripts volume
```

개발 흐름:

```text
1. 내 Mac에서 n8n workflow와 Python 스크립트를 만든다.
2. 잘 돌면 GitHub에 push한다.
3. VPS에서 pull한다.
4. VPS의 Docker Compose가 n8n을 24시간 실행한다.
5. n8n Schedule Trigger가 Asia/Seoul 기준 오전 7시에 돈다.
```

## Concept Map

### n8n

n8n은 자동화 스케줄러이자 파이프라인 도구다.

이 프로젝트에서 n8n은 다음 일을 맡는다.

- 매일 오전 7시에 자동 실행
- Claude Agent SDK 탐색 스크립트 실행
- 결과를 Telegram, Slack, Notion, email 중 하나로 전송
- 실패하면 로그 남기기

n8n은 똑똑한 판단을 하는 곳이 아니다. 실행 순서를 관리하는 곳이다.

### Claude Agent SDK

Claude Agent SDK는 탐색하고 판단하는 에이전트다.

이 프로젝트에서 Claude Agent SDK는 다음 일을 맡는다.

- 오늘의 관심사와 최근 피드백을 읽는다.
- 웹과 공개 소스를 탐색한다.
- 좋은 방향이 보이면 더 깊게 파고든다.
- 별로면 다른 방향으로 전환한다.
- 내 관심사와 성향에 맞는지 평가한다.
- 왜 추천하는지 설명한다.
- 오늘 바로 할 수 있는 작은 행동을 제안한다.
- 최종 TOP 5 브리프를 만든다.

Claude Agent SDK는 스케줄러가 아니다. 판단과 reasoning을 담당한다.

### Paperclip UI

Paperclip UI는 관제실이다.

이 프로젝트에서 Paperclip UI는 다음 일을 보여준다.

- 오늘 실행 성공 여부
- 관심사별 내부 Agent 상태
- 탐색한 방향
- 발견한 아이템 수
- 추천된 TOP 5
- 추천 이유
- 실패 로그
- 내가 저장하거나 다시 보고 싶은 아이템

초기에는 UI를 크게 만들지 않는다. 먼저 Claude Agent SDK가 흥미로운 탐색 결과를 만들고, Paperclip에서 그 결과에 피드백을 줄 수 있게 만든다.

## Target Architecture

```text
Daily Schedule: 07:00
        |
        v
      n8n
        |
        +-- Run daily exploration agent
        |
        v
Claude Agent SDK
        |
        +-- web search
        +-- source reading
        +-- direction pivot
        +-- taste-based curation
        |
        v
Daily Brief JSON / Markdown / UI Cards
        |
        +-- SQLite 저장
        +-- Telegram or Slack 전송
        +-- Paperclip UI에서 조회
```

## Data Flow

### 1. Explore

Claude Agent SDK가 직접 탐색한다.

처음에는 고정 수집기를 많이 만들지 않는다. Agent가 관심사, 최근 피드백, 오늘의 탐색 목표를 읽고 웹을 둘러본다.

탐색 중 좋은 방향이 보이면 더 깊게 파고든다.

```text
AI agent 사례 탐색
  -> incident response 자동화 발견
  -> backend 장애 분석 관심사와 맞음
  -> AI incident triage 사례를 더 탐색
  -> GitHub repo, HN discussion, 실무 글까지 확장
```

### 2. Curate

Claude Agent SDK가 탐색 결과를 큐레이션한다.

중요한 질문:

- 이게 지금 나를 움직이게 하는가?
- AI, 백엔드, 자동화, 영감 주는 사람과 연결되는가?
- 오늘 30분 안에 뭔가 해볼 수 있는가?
- 블로그, 프로젝트, 자동화, 수익화 실험으로 확장되는가?

### 3. Save

결과를 저장한다.

초기 저장소는 SQLite가 적당하다.

저장할 것:

- 실행 날짜
- 탐색 결과 아이템
- TOP 5 결과
- 관심사별 내부 Agent 상태
- 실패 로그

### 4. Package

결과를 읽고 싶게 포장한다.

단순 링크 목록이 아니라, 호기심을 일으키는 콘텐츠로 만든다.

출력 포맷:

- Morning Signal
- Paperclip Cards
- Deep Dive 후보
- 오늘 바로 할 30분 행동
- 나중에 콘텐츠로 만들 만한 angle

### 5. Send

매일 아침 결과를 보낸다.

추천 순서:

1. Telegram
2. Slack
3. Email
4. Notion

처음에는 Telegram이 가장 가볍다.

### 6. Observe

Paperclip UI에서 본다.

초기 화면:

```text
Inspiration Engine

AI Agent             green
Backend Agent        green
Money Agent          green
People Agent         green
Curation Agent       green

Today:
- discoveries: 32
- selected: 5
- sent: yes
- failed sources: 1
```

## Phase Plan

### Phase 0: Local Foundation

목표:

n8n 화면을 열고, 프로젝트 구조를 만든다.

완료 기준:

- n8n이 `http://localhost:5678`에서 열린다.
- README와 계획 문서가 있다.
- Claude Agent SDK 샘플 스크립트가 있다.

현재 상태:

대부분 완료.

### Phase 1: Claude Exploration Agent

목표:

Claude Agent SDK가 직접 탐색하고 TOP 5를 만든다.

구현:

- 관심사와 최근 피드백 prompt 작성
- `explore_daily.py` 실행
- Claude Agent SDK web search / web read 허용
- 결과를 Markdown으로 저장

완료 기준:

- 터미널에서 오늘의 탐색 결과 TOP 5가 출력된다.
- 결과가 `data/briefs/YYYY-MM-DD.md`에 저장된다.

### Phase 2: n8n Daily Run - Local Test

목표:

n8n이 로컬에서 Python 스크립트를 실행한다.

구현:

- n8n Schedule Trigger
- Execute Command node
- `python3 scripts/explore_daily.py`
- 결과 파일 저장

완료 기준:

- n8n에서 수동 실행이 성공한다.
- 오전 7시 자동 실행 설정이 있다.
- 실패 로그를 볼 수 있다.

주의:

이 단계의 오전 7시 실행은 노트북과 Docker가 켜져 있을 때만 동작한다.

### Phase 2.5: VPS Deployment

목표:

Paper Company가 실제로 매일 오전 7시에 자동 실행되도록 작은 서버에 올린다.

구현:

- VPS 생성
- Docker와 Docker Compose 설치
- repo clone
- `.env` 설정
- `docker compose up -d`
- n8n workflow import
- timezone을 `Asia/Seoul`로 고정

완료 기준:

- 내 노트북이 꺼져 있어도 n8n이 켜져 있다.
- 서버의 n8n에서 오전 7시 Schedule Trigger가 동작한다.
- Telegram 테스트 메시지가 서버에서 전송된다.

### Phase 3: Better Exploration

목표:

탐색 품질을 높인다.

처음 강화할 탐색 영역:

- GitHub Trending
- Hacker News
- 개발자 RSS
- AI startup RSS/newsletter

나중에 붙일 소스:

- YouTube
- Instagram trend
- personal notes

완료 기준:

- 매일 다른 방향의 흥미로운 발견이 나온다.
- 결과마다 왜 그 방향을 더 팠는지 reasoning이 남는다.

### Phase 4: Telegram Delivery

목표:

매일 아침 메시지를 받는다.

구현:

- Telegram bot 생성
- n8n Telegram node 연결
- Daily Brief Markdown 전송

완료 기준:

- 오전 7시에 Telegram으로 TOP 5가 온다.

### Phase 4.5: Telegram Command Interface

목표:

모바일에서 Paper Company에게 실시간으로 일을 시킨다.

구현:

- Telegram bot 생성
- n8n Telegram Trigger 또는 Webhook 연결
- `/ping`
- `/save`
- `/feedback`
- `/incident`
- `/ask`

완료 기준:

- 모바일에서 `/ping`을 보내면 응답한다.
- `/incident`로 장애 상황을 보내면 Claude Agent SDK가 관련 기술 글과 체크리스트를 찾아준다.
- 요청과 답변이 SQLite에 저장된다.

### Phase 5: Paperclip UI MVP

목표:

살아 움직이는 느낌을 주는 관제실을 만든다.

초기 화면:

- Agent status
- Today TOP 5
- source별 발견 수
- 탐색 경로
- latest run time
- failures

기술:

- FastAPI or simple Python backend
- SQLite
- HTML/CSS/JS or React

완료 기준:

- 브라우저에서 오늘 실행 결과를 볼 수 있다.
- Agent 카드를 클릭하면 추천 이유와 로그를 볼 수 있다.

### Phase 6: Feedback Loop MVP

목표:

내가 실제로 꽂힌 아이템을 시스템이 학습하게 만든다.

구현:

- `saved`
- `not_interested`
- `acted_on`
- `turned_into_content`

완료 기준:

- 내가 누른 피드백이 다음 exploration prompt에 반영된다.

### Phase 7: Real-Time Re-ranking

목표:

Paperclip에서 피드백을 준 즉시 다시 추천받을 수 있게 만든다.

구현:

- Paperclip의 `Re-rank` 버튼
- 최근 피드백 로딩
- 오늘 탐색 결과 재사용
- Claude Agent SDK 즉시 호출
- 새 TOP 5를 UI에 표시

완료 기준:

- 마음에 안 드는 추천에 피드백을 준다.
- 버튼을 누르면 같은 탐색 결과에서 더 내 취향에 맞는 TOP 5가 다시 나온다.

## Recommended Build Order

1. Claude Agent SDK로 매일 탐색 브리프 만들기
2. 결과를 Markdown/JSON 파일로 저장하기
3. n8n에서 버튼 눌러 실행하기
4. n8n에서 매일 오전 7시 자동 실행하기
5. Telegram으로 보내기
6. Telegram `/ping` 명령 만들기
7. SQLite에 실행 기록 저장하기
8. Paperclip UI에서 실행 결과 보기
9. Telegram `/incident` 실시간 탐색 만들기
10. Paperclip UI에서 피드백 저장하기
11. 피드백을 다음 exploration prompt에 반영하기
12. GitHub/HN/RSS는 필요할 때 보조 소스로 안정화하기
13. YouTube/Instagram/People 탐색 능력 확장하기
14. Re-rank 버튼으로 실시간 재추천하기

## First Milestone

가장 첫 번째 마일스톤은 작다.

```text
관심사 + 최근 피드백
  -> Claude Agent SDK exploratory search
  -> 흥미롭게 읽히는 오늘의 영감 TOP 5 저장
  -> n8n에서 버튼 눌러 실행
```

이게 되면 시스템은 이미 살아 움직이기 시작한 것이다.
