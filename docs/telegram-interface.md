# Telegram Interface

Telegram bot은 Paper Company의 모바일 명령창이다.

Morning Signal은 매일 오전 7시에 자동으로 받는 브리프이고, Telegram Interface는 내가 필요할 때 즉시 Paper Company에게 일을 시키는 입구다.

## Why Telegram

Telegram을 쓰는 이유:

- 모바일에서 바로 질문할 수 있다.
- n8n webhook과 연결하기 쉽다.
- Paper Company의 Claude Agent SDK 스크립트를 실행시킬 수 있다.
- 질문과 답변을 SQLite에 저장할 수 있다.
- 나중에 Paperclip UI에서 히스토리를 볼 수 있다.

## Use Cases

### 1. Incident Search

장애나 이상 현상이 생겼을 때 바로 묻는다.

예:

```text
/incident
Redis connection timeout이 갑자기 늘었어.
Spring Boot + Lettuce 쓰고 있고, 최근 pool 설정을 바꿨어.
관련 기술 블로그나 장애 분석 글 찾아줘.
```

Paper Company가 해야 할 일:

- 증상을 구조화한다.
- 관련 키워드를 뽑는다.
- LINE/LY, 우아한형제들, NAVER D2, Google Developers, GitHub Issues 등을 우선 탐색한다.
- 가능한 원인 후보를 정리한다.
- 바로 확인할 체크리스트를 준다.
- 참고 링크를 붙인다.

### 2. Ask Research

특정 기술이나 아이디어를 바로 조사한다.

예:

```text
/ask
Claude Agent SDK로 장애 로그 triage agent 만들 수 있을까?
비슷한 사례와 첫 구현 방법 찾아줘.
```

### 3. Save Idea

떠오른 아이디어를 저장한다.

예:

```text
/save
Paperclip에 Re-rank 버튼 만들기. 피드백 반영해서 같은 후보를 다시 큐레이션.
```

### 4. Feedback

아침에 받은 Morning Signal에 피드백을 준다.

예:

```text
/feedback
오늘 2번 좋았음. 바로 Paper Company에 붙일 수 있는 느낌이라 좋았다.
```

## Architecture

```text
Telegram mobile app
  |
  v
Telegram Bot
  |
  v
n8n Webhook
  |
  +-- route command
        |
        +-- /incident -> scripts/incident_search.py
        +-- /ask      -> scripts/ask_research.py
        +-- /save     -> SQLite insert
        +-- /feedback -> SQLite insert
  |
  v
Claude Agent SDK
  |
  v
SQLite + Telegram response
```

## n8n Workflow

초기 n8n workflow:

```text
Telegram Trigger
  -> Switch command
  -> Execute Command
  -> Read output
  -> Telegram Send Message
```

명령어별 처리:

```text
/incident
  -> .venv/bin/python scripts/incident_search.py --text "$MESSAGE"

/ask
  -> .venv/bin/python scripts/ask_research.py --text "$MESSAGE"

/save
  -> .venv/bin/python scripts/save_note.py --text "$MESSAGE"

/feedback
  -> .venv/bin/python scripts/save_feedback.py --text "$MESSAGE"
```

## SQLite Records

저장할 데이터:

```text
mobile_requests
  id
  command
  input_text
  response_text
  created_at

incident_searches
  id
  symptom
  context
  suspected_causes
  checklist
  sources
  created_at
```

## Phase Plan

### Phase T1: Bot Skeleton

목표:

Telegram에서 `/ping`을 보내면 Paper Company가 응답한다.

완료 기준:

```text
/ping -> pong from Paper Company
```

### Phase T2: Save Commands

목표:

`/save`, `/feedback`을 SQLite에 저장한다.

완료 기준:

- 모바일에서 보낸 텍스트가 DB에 남는다.
- Paperclip에서 나중에 볼 수 있다.

### Phase T3: Incident Search

목표:

장애 상황을 입력하면 Claude Agent SDK가 실시간 탐색한다.

완료 기준:

- `/incident` 입력
- 관련 기술 포스팅 탐색
- 원인 후보와 체크리스트 반환
- 결과를 SQLite에 저장

### Phase T4: Paperclip History

목표:

Telegram으로 요청한 히스토리를 Paperclip UI에서 본다.

완료 기준:

- 요청 목록
- 답변
- 참고 링크
- 후속 피드백

