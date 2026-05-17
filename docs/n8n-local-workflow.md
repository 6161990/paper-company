# n8n Local Workflow

로컬 n8n에서 Paper Company 탐색 스크립트를 실행하는 방법이다.

## Important Constraint

기본 `n8nio/n8n` 컨테이너에는 Python이 없다.

또한 Claude Agent SDK는 로컬 Claude Code 로그인/권한 상태를 사용한다.

그래서 로컬 MVP에서는 n8n이 Python을 직접 실행하지 않는다. 대신 호스트 Mac에서 작은 local runner를 띄우고, n8n이 HTTP로 runner를 호출한다.

## Start n8n

```bash
docker compose up -d
```

## Start Local Runner

별도 터미널에서 local runner를 띄운다.

```bash
.venv/bin/python scripts/local_runner.py
```

이 터미널은 n8n workflow를 실행하는 동안 계속 켜둔다.

확인:

```bash
curl http://127.0.0.1:8711/health
```

## n8n HTTP Request

n8n workflow에서는 `Execute Command` 대신 `HTTP Request` 노드를 쓴다.

설정:

```text
Method: POST
URL: http://host.docker.internal:8711/run/explore
Response Format: JSON
```

이렇게 하면 n8n 컨테이너가 Mac의 local runner를 호출하고, local runner가 호스트의 `.venv`와 Claude Code 로그인 상태로 `explore_daily.py`를 실행한다.

## Workflow Shape

```text
Manual Trigger
  -> HTTP Request POST http://host.docker.internal:8711/run/explore
  -> Inspect response stdout
```

다음 단계:

```text
Schedule Trigger 07:00
  -> HTTP Request
  -> Telegram Send Message
```

## SQLite Access

스크립트가 실행되면 결과는 다음에 저장된다.

```text
data/briefs/YYYY-MM-DD.md
data/paper_company.db
```
