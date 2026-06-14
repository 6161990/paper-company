# Railway 배포 가이드

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ Railway (cloud.railway.app)                         │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Cron Job (매일 7AM KST)                        │ │
│ │ ANTHROPIC_API_KEY로 explore_daily.py 실행    │ │
│ │ → Morning Signal 생성 & /data/paper_company.db │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Services (24/7 Always-On)                      │ │
│ │ - runner (:8711) - Telegram /run 처리          │ │
│ │ - telegram_poll - Telegram polling             │ │
│ │ - paperclip (:8720) - Paperclip UI             │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Volume (/data)                                 │ │
│ │ SQLite DB + briefs 마크다운 영구 저장         │ │
│ └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘


로컬 맥북 (개발용)
├─ Claude Agent SDK (git push할 때만 필요)
├─ explore_daily.py 수동 테스트
└─ git push → Railway 자동 배포
```

---

## Railway 배포 (자동 7AM 실행)

### 1️⃣ Variables 설정

Railway 대시보드 → Variables 탭

```
TELEGRAM_BOT_TOKEN = (BotFather 토큰)
DB_PATH = /data/paper_company.db
ANTHROPIC_API_KEY = sk-ant-xxxx... (https://console.anthropic.com/account/keys)
```

### 2️⃣ Volume 추가

Railway 대시보드 → Settings → Storage

```
Mount Path: /data
Size: 5GB
```

### 3️⃣ Cron Job 설정

Railway 대시보드 → Cron Jobs → Create New

```
Name: paper-company-morning-signal
Schedule: 0 22 * * *  (7AM KST = UTC 10PM 전날)
Command: python scripts/explore_daily.py
```

**시간대 주의:**
- 한국 시간 7AM = UTC 10PM (전날 밤)
- 따라서 `0 22 * * *` (저녁 10시)

### 4️⃣ Procfile 확인

프로젝트 루트에 `Procfile` 있는지 확인:

```
runner: python scripts/local_runner.py
ui: python scripts/paperclip_server.py
telegram: python scripts/telegram_poll.py
```

### 5️⃣ GitHub Push

```bash
git push origin main
```

Railway가 자동 감지 → 배포 시작

---

## 로컬에서 테스트

### 로컬 설정

#### 1. Claude Agent SDK 설정 (로컬 개발용)

```bash
# 설치
pip install claude-agent-sdk

# Claude Code 로그인
claude
# CLI에서 /login 실행
# 브라우저에서 로그인 후 ~/.claude 생성
```

#### 2. explore_daily.py 실행

```bash
cd ~/Documents/GitHub/paper-company

# 로컬에서 실행 (자동으로 SDK 사용)
.venv/bin/python scripts/explore_daily.py
```

**자동으로 선택:**
```
- ANTHROPIC_API_KEY 환경변수 없음 → Claude Agent SDK 사용
- ~/.claude 있으면 → 인증 성공
- 없으면 → 로그인 안 됨 에러
```

#### 3. 로컬 crontab (선택사항)

로컬 맥북에서도 매일 7AM 자동 실행:

```bash
crontab -e
```

추가:

```bash
# 매일 7AM KST에 explore_daily.py 실행
0 7 * * * /Users/j6161990/Documents/GitHub/paper-company/.venv/bin/python /Users/j6161990/Documents/GitHub/paper-company/scripts/explore_daily.py >> /tmp/paper-company-cron.log 2>&1
```

확인:

```bash
tail -f /tmp/paper-company-cron.log
```

---

## 코드 동작 방식

### explore_daily.py 로직

```python
if ANTHROPIC_API_KEY 환경변수 있음:
    main_api() 실행 (Anthropic API)
    ↓
    Anthropic SDK로 Claude API 직접 호출
    ↓
    Morning Signal 생성
else:
    main_sdk() 실행 (Claude Agent SDK)
    ↓
    ~/.claude 인증 정보 사용
    ↓
    claude_agent_sdk로 웹 탐색 (WebSearch, WebFetch)
    ↓
    Morning Signal 생성
```

**Railway:** `ANTHROPIC_API_KEY` 환경변수 설정 → `main_api()` 자동 선택
**로컬:** 환경변수 없음 → `main_sdk()` 자동 선택

---

## Morning Signal 데이터 흐름

### Railway Cron Job (매일 7AM)

```
Cron Job 트리거
  ↓
python scripts/explore_daily.py
  ↓
ANTHROPIC_API_KEY로 Morning Signal 생성
  ↓
/data/briefs/2026-06-14.md 저장
  ↓
SQLite /data/paper_company.db 저장
  ↓
Telegram bot이 조회 가능
  ↓
Paperclip UI에 표시
```

### 로컬 테스트

```
.venv/bin/python scripts/explore_daily.py
  ↓
Claude Agent SDK로 Morning Signal 생성
  ↓
data/briefs/2026-06-14.md 저장 (로컬)
  ↓
SQLite data/paper_company.db 저장 (로컬)
  ↓
로컬 SQL만 업데이트 (Railway와 별개)
```

---

## 테스트 체크리스트

### Railway 배포 확인

```bash
cloud.railway.app
→ Deployments: 최신 배포 "Complete" 상태인지 확인
→ Logs: 오류 없는지 확인
→ Cron Jobs: 최근 실행 로그 확인
```

### Telegram 테스트

```
/ping   → "pong from Paper Company"
/today  → 최신 Morning Signal
/run    → 새로운 Signal 생성 (2-3분)
```

### Paperclip UI

```bash
# Railway 도메인으로 접근
https://your-railway-domain/

# 또는 SSH 터널 (로컬)
ssh -L 8720:127.0.0.1:8720 paper@railway-domain
# 브라우저: http://127.0.0.1:8720
```

---

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| Cron Job 실행 안 됨 | Schedule 시간대 오류 | `0 22 * * *` (7AM KST = UTC 10PM) 확인 |
| Anthropic API 오류 | ANTHROPIC_API_KEY 미설정 | Variables에서 API Key 추가 |
| Morning Signal 안 보임 | Volume 미설정 | Volume 추가 (/data, 5GB) |
| 로컬 SDK 로그인 실패 | ~/.claude 없음 | `claude` → `/login` 실행 |

---

## 필요한 API Key

### Anthropic API Key

1. https://console.anthropic.com/account/keys 방문
2. "Create Key" 버튼 클릭
3. API Key 복사: `sk-ant-xxxxx...`
4. Railway Variables에 추가

### Telegram Bot Token

1. Telegram @BotFather와 대화
2. `/newbot` 명령
3. 봇 이름 설정
4. 받은 토큰 복사
5. Railway Variables에 추가

---

## 배포 후 코드 수정

코드를 수정하고 push하면 Railway 자동 배포:

```bash
# 코드 수정
vim scripts/explore_daily.py

# 커밋 & 푸시
git add .
git commit -m "Fix: something"
git push origin main

# Railway가 자동으로:
# 1. GitHub webhook 감지
# 2. 새 빌드 시작
# 3. Procfile 프로세스 시작
# 4. Cron Job 활성화
```

---

## 정리

**Railway = 운영 환경**
- 24/7 서비스 (telegram, runner, UI)
- 매일 7AM Cron으로 Morning Signal 생성
- ANTHROPIC_API_KEY로 자동 실행

**로컬 맥북 = 개발 환경**
- 수동 테스트 (Claude Agent SDK)
- git push로 Railway 배포 트리거
- 선택사항: crontab으로 로컬에서도 자동 실행

---

## 다음 단계

1. Anthropic API Key 발급 (console.anthropic.com)
2. Railway Variables 설정 (ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN)
3. Volume 추가 (/data, 5GB)
4. Cron Job 설정 (0 22 * * *)
5. `git push origin main` 배포
6. Telegram `/ping` 테스트
