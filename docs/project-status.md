# Paper Company Project Status

이 문서는 Paper Company의 프로젝트 관리자 보드다.

목표는 두 가지다.

1. 지금 어디까지 왔는지 한눈에 본다.
2. Paper Company를 온라인에서 매일 받아보기 위해 남은 기술 작업을 구분한다.

## Current Goal

```text
내 노트북이 꺼져 있어도
매일 오전 7시에
Paper Company가 탐색하고
Telegram으로 Morning Signal을 보내고
Paperclip에서 결과와 피드백을 볼 수 있게 만든다.
```

## System Map

```text
                 ┌─────────────────────┐
                 │  Telegram Mobile     │
                 │  - Morning Signal    │
                 │  - /feedback         │
                 └──────────┬──────────┘
                            │
                            v
┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
│   n8n         │────▶│ Python       │────▶│ Claude Agent SDK    │
│ - 7AM trigger │     │ scripts      │     │ - web search        │
│ - webhook     │     │              │     │ - web fetch         │
│ - routing     │     │              │     │ - curation          │
└──────┬───────┘     └──────┬───────┘     └─────────┬──────────┘
       │                    │                       │
       v                    v                       v
┌──────────────────────────────────────────────────────────────┐
│ SQLite                                                       │
│ - Morning Signal                                             │
│ - feedback                                                   │
│ - mobile requests                                            │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               v
                    ┌─────────────────────┐
                    │ Paperclip UI         │
                    │ - TOP 5 cards        │
                    │ - feedback buttons   │
                    │ - logs/history       │
                    └─────────────────────┘
```

## Status By Area

```text
Legend:
[x] done
[~] partially done
[ ] not started
```

| Area | Status | Meaning |
|---|---:|---|
| Project direction | [x] | Paper Company concept is defined |
| Claude Agent SDK install | [x] | SDK installed in `.venv` |
| Exploration script | [~] | `explore_daily.py` exists; needs repeated real-run validation |
| Korean output | [x] | Prompt requires Korean Morning Signal |
| Backend source priority | [x] | LY/LINE, Woowahan, Google Developers, NAVER D2 added |
| Interest balance guard | [x] | Prompt limits AI/backend overrepresentation and requires Money/People items |
| Markdown brief save | [x] | Saves to `data/briefs/YYYY-MM-DD.md` |
| n8n local | [x] | Docker Compose exists and n8n can run locally |
| SQLite | [x] | Briefs and TOP 5 items are saved to SQLite |
| Paperclip UI | [~] | Local MVP shows Morning Signal, run state, logs, and feedback history |
| n8n workflow | [~] | Local runner path verified; n8n UI workflow/manual trigger still needs final confirmation |
| Telegram delivery | [x] | Local polling bot can send `/today` and `/run` results |
| Telegram commands | [~] | Local polling bot supports `/ping`, `/today`, `/run`, `/save`, `/feedback`; `/ask` pending |
| VPS deployment | [~] | Deployment guide and systemd units exist; actual server setup pending |

## Critical Path To Online Morning Signal

온라인에서 매일 받아보려면 이 순서가 필요하다.

```text
1. Local script works
   ↓
2. Save result to SQLite
   ↓
3. n8n runs script locally
   ↓
4. Telegram bot sends result
   ↓
5. Deploy n8n + scripts + SQLite to VPS
   ↓
6. VPS n8n runs every 7AM
   ↓
7. Paperclip UI reads SQLite
```

## Work That Can Proceed Before Quality Tuning

아래 작업들은 Morning Signal의 취향/품질 튜닝과 독립적으로 진행할 수 있다.

### 1. SQLite Foundation

목표:

추천 결과, 피드백, 모바일 요청을 저장할 DB를 만든다.

작업:

```text
[x] create `paper_company.db`
[x] create `briefs` table
[x] create `items` table
[x] create `feedback` table
[x] create `mobile_requests` table
[x] create `run_logs` table
[x] create DB helper module
[x] save Morning Signal to `briefs`
[x] parse TOP 5 into `items`
```

완료 기준:

```text
explore_daily.py 실행 결과가 Markdown, SQLite `briefs`, SQLite `items` 테이블에 저장된다.
```

### 2. n8n Local Workflow

목표:

n8n 버튼 또는 수동 실행으로 `explore_daily.py`를 실행한다.

작업:

```text
[x] create local runner
[x] verify runner health endpoint
[x] verify n8n can reach runner via `host.docker.internal`
[~] create n8n workflow in UI
[~] add Manual Trigger
[~] add HTTP Request node
[~] POST `http://host.docker.internal:8711/run/explore`
[ ] confirm full successful run from n8n UI
[x] inspect success/failure logs in Paperclip after local runner execution
```

완료 기준:

```text
n8n에서 버튼을 누르면 local runner가 호출되고 Morning Signal 파일/SQLite record가 생성된다.
```

### 3. Telegram Bot Skeleton

목표:

모바일에서 Paper Company가 응답하는지 확인한다.

작업:

```text
[x] create Telegram bot with BotFather
[x] store bot token in `.env`
[x] run `scripts/telegram_poll.py`
[x] implement local `/ping` handler
[x] implement local `/today` handler
[x] implement local `/run` handler
[x] implement local `/save` handler
[x] implement local `/feedback` handler
[x] store mobile requests in SQLite
[x] store feedback in SQLite
[ ] connect n8n Telegram Trigger later
```

완료 기준:

```text
/ping -> pong from Paper Company
```

현재 확인:

```text
/start, /ping, /today, /run, /help, /save, /feedback 요청이 `mobile_requests`에 저장됨.
```

### 4. Telegram Morning Signal Delivery

목표:

생성된 Morning Signal을 Telegram으로 보낸다.

작업:

```text
[x] read latest SQLite brief
[x] send message to Telegram
[x] handle long message splitting
```

완료 기준:

```text
Morning Signal이 Telegram으로 도착한다.
```

현재는 로컬 polling bot 기준으로 완료됐다. 온라인 운영에서는 VPS 또는 n8n Telegram Trigger로 옮겨야 한다.

### 5. Paperclip UI MVP

목표:

SQLite에 저장된 결과를 브라우저에서 본다.

작업:

```text
[x] backend endpoint: latest brief
[x] page: Morning Signal
[x] cards: TOP 5
[x] buttons: Like / Dislike / Save / Acted
[x] store feedback
[x] run status integration
[x] logs/history view
[x] feedback history view
[x] item-level feedback polish
```

완료 기준:

```text
브라우저에서 오늘 결과를 보고 버튼으로 피드백을 저장할 수 있다.
```

현재 로컬 실행:

```bash
.venv/bin/python scripts/paperclip_server.py
```

```text
http://127.0.0.1:8720
```

### 6. VPS Deployment

목표:

내 노트북이 꺼져 있어도 Paper Company가 돈다.

작업:

```text
[ ] choose VPS
[ ] install Docker
[ ] clone repo
[ ] configure `.env`
[ ] Claude auth on VPS
[ ] install systemd services
[ ] run n8n on VPS
[ ] test Telegram delivery from VPS
[ ] add 7AM schedule
```

완료 기준:

```text
VPS에서 오전 7시에 자동 실행되고 Telegram으로 도착한다.
```

## Suggested Next 3 Moves

품질 튜닝 없이 바로 진행 가능한 순서:

```text
1. Confirm full successful Morning Signal run from n8n UI
2. Polish Paperclip feedback/history views
3. Deploy to VPS for 7AM automation
```

이 세 개가 되면 Paper Company는 단순 스크립트가 아니라 관리 가능한 시스템이 된다.

## Not Blocking Yet

아래는 중요하지만 지금 당장 막고 있지는 않다.

```text
- Morning Signal 품질 튜닝
- Paperclip 디자인 완성도
- VPS 선택
- 실시간 Re-rank
- 장기 피드백 학습
```

## Decision Needed

다음 구현을 시작하려면 하나만 고르면 된다.

```text
Option A: n8n UI에서 성공 실행을 최종 확인한다.
Option B: Paperclip UI MVP를 만든다.
Option C: VPS 배포 준비를 시작한다.
```

추천은 `Option A -> Option B -> Option C`다. n8n 실행 경로를 확정한 뒤 UI에서 결과와 피드백을 관리하고, 마지막에 온라인 운영으로 옮긴다.
