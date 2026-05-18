# Telegram Interface

Telegram bot은 Paper Company의 모바일 명령창이다.

Morning Signal은 매일 오전 7시에 자동으로 받는 브리프이고, Telegram Interface는 내가 필요할 때 즉시 Paper Company에게 일을 시키는 입구다.

## Why Telegram

Telegram을 쓰는 이유:

- 모바일에서 바로 질문할 수 있다.
- Paper Company의 Claude Agent SDK 스크립트를 실행시킬 수 있다.
- 질문과 답변을 SQLite에 저장할 수 있다.
- 나중에 Paperclip UI에서 히스토리를 볼 수 있다.

## Commands

현재 지원:

```text
/ping   - 연결 확인
/today  - 최신 Morning Signal 받기
/run    - 새 Morning Signal 생성 후 받기
/save   - 아이디어 저장
/feedback - Morning Signal 피드백 저장
/help   - 명령어 보기
```

준비 중:

```text
/ask      - 리서치 요청
```

## Architecture

현재 로컬 구조:

```text
Telegram mobile app
  |
  v
scripts/telegram_poll.py
  |
  +-- /today -> SQLite latest brief
  +-- /run   -> scripts/explore_daily.py
  +-- /save  -> SQLite feedback
  +-- /feedback -> SQLite feedback + recent_feedback.json
  +-- /ping  -> pong
  |
  v
SQLite
```

나중에 온라인 구조:

```text
Telegram Bot
  |
  v
n8n Telegram Trigger
  |
  v
Paper Company scripts
  |
  v
SQLite + Telegram response
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

feedback
  id
  item_id
  brief_id
  feedback_type
  note
  created_at
```

## Phase Plan

### Phase T1: Bot Skeleton

완료 기준:

```text
/ping -> pong from Paper Company
```

### Phase T2: Morning Signal Commands

완료 기준:

```text
/today -> 최신 Morning Signal 전송
/run   -> 새 Morning Signal 생성 후 전송
```

### Phase T3: Save Commands

목표:

`/save`, `/feedback`을 SQLite에 저장한다.

완료 기준:

- 모바일에서 보낸 텍스트가 DB에 남는다.
- 피드백이 `feedback` 테이블에 남는다.
- 다음 Morning Signal이 읽는 `paper_company/recent_feedback.json`이 갱신된다.
- Paperclip에서 나중에 볼 수 있다.

### Phase T4: Paperclip History

목표:

Telegram으로 요청한 히스토리를 Paperclip UI에서 본다.

완료 기준:

- 요청 목록
- 답변
- 후속 피드백
