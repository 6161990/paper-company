# Paper Company

영감 기반 AI 콘텐츠 공장 + 관제실입니다.

목적은 콘텐츠 자동 생산보다 먼저, AI가 매일 나 대신 세상을 둘러보고 나에게 꽂힐 가능성이 높은 아이템을 가져오게 하는 것입니다.

## Current Local Run Order

현재 로컬에서는 n8n이 Python을 직접 실행하지 않는다.

```text
n8n
  -> HTTP Request
  -> local runner
  -> Claude Agent SDK
  -> Markdown + SQLite 저장
```

### 1. Start n8n

```bash
cp .env.example .env
docker compose up -d
```

n8n:

```text
http://localhost:5678
```

### 2. Start Local Runner

다른 터미널에서 실행한다.

```bash
.venv/bin/python scripts/local_runner.py
```

이 터미널은 n8n workflow를 실행하는 동안 계속 켜둔다.

확인:

```bash
curl http://127.0.0.1:8711/health
```

정상 응답:

```json
{"ok": true, "service": "paper-company-runner"}
```

### 3. Run From n8n

n8n에서 workflow를 만든다.

```text
Manual Trigger
  -> HTTP Request
```

HTTP Request 설정:

```text
Method: POST
URL: http://host.docker.internal:8711/run/explore
Response Format: JSON
```

성공하면 결과가 저장된다.

```text
data/briefs/YYYY-MM-DD.md
data/paper_company.db
```

## Direct Script Run

n8n 없이 바로 실행할 수도 있다.

```bash
.venv/bin/python scripts/explore_daily.py
```

## Paperclip UI

SQLite에 저장된 Morning Signal과 피드백을 브라우저에서 본다.

```bash
.venv/bin/python scripts/paperclip_server.py
```

브라우저:

```text
http://127.0.0.1:8720
```

현재 기능:

```text
- 최신 Morning Signal TOP 5 카드
- Source / Why Now / Why Fit / Next Action / Expansion / Exploration Path
- Save / Like / Dislike / Acted / Content 피드백 버튼
- 전체 Morning Signal 피드백 입력
- n8n/local runner 실행 상태 표시
- 실행 로그 표시
- 최근 피드백 표시
```

## SQLite

DB 열기:

```bash
sqlite3 data/paper_company.db
```

최근 브리프 확인:

```sql
SELECT id, run_date, title FROM briefs ORDER BY run_date DESC;
```

자세한 내용:

[SQLite Access](docs/sqlite-access.md)

## Stop Services

```bash
docker compose down
```

local runner는 실행 중인 터미널에서 `Ctrl+C`로 종료한다.

## MVP Direction

- Local Runtime: 하나의 Claude Agent SDK 실행
- Internal Agents: AI, Backend, Stock/Business, Inspiring People
- 역할: 관심사별 탐색, 방향 전환, 큐레이션, TOP 5 추천

## Product Notes

- [Project Status](docs/project-status.md)
- [n8n Local Workflow](docs/n8n-local-workflow.md)
- [SQLite Access](docs/sqlite-access.md)
- [Vision](docs/vision.md)
- [Roadmap](docs/roadmap.md)
- [Runtime Plan](docs/runtime-plan.md)
- [Feedback Loop](docs/feedback-loop.md)
- [Telegram Interface](docs/telegram-interface.md)
- [Output Experience](docs/output-experience.md)
- [Agent Map](docs/agent-map.md)
- [Daily Brief Format](docs/daily-brief-format.md)
