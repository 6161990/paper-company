# Railway 배포 가이드

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ Railway (cloud.railway.app)                         │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Service 1: paper-company (Always-On)          │ │
│ │                                                │ │
│ │ - paper-company-runner (:8711)                │ │
│ │   └─ Telegram /run 명령 처리                  │ │
│ │                                                │ │
│ │ - paper-company-telegram                      │ │
│ │   └─ Telegram polling (메시지 수신)           │ │
│ │                                                │ │
│ │ - paperclip (:8720)                           │ │
│ │   └─ Paperclip UI                            │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Cron Job: paper-company-daily                 │ │
│ │ 매일 7AM UTC → explore_daily.py 실행          │ │
│ │ Morning Signal 생성 & SQLite 저장             │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ SQLite Volume (/data)                         │ │
│ │ 영구 저장소 (5GB)                             │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ Python 3.11                                         │
└─────────────────────────────────────────────────────┘
         ↑↓
   GitHub Auto-Deploy
   (push → 자동 배포)
   
         ↑↓
    Telegram API
    (/ping, /today, /run)
```

## 배포 흐름

```
GitHub에 push
    ↓
Railway가 자동 감지
    ↓
Webhook 트리거
    ↓
새 버전 빌드 & 배포
    ↓
Docker 이미지로 실행
    ↓
서비스 시작 (Bot + HTTP servers)
    ↓
Cron job 대기 (7AM에 Morning Signal 생성)
```

## 배포 단계

### 1. Railway 가입

```bash
cloud.railway.app
GitHub로 로그인 (추천)
```

### 2. 새 프로젝트 생성

```bash
Dashboard → Create Project → GitHub Repo
paper-company 리포지토리 선택
```

→ Railway가 자동으로 GitHub 연결

### 3. 환경 변수 설정

```bash
Railway 프로젝트 → Variables 탭

TELEGRAM_BOT_TOKEN = xxx (BotFather에서 발급)
TELEGRAM_CHAT_ID = xxx (선택사항)
```

### 4. SQLite Volume 추가

```bash
Railway 프로젝트 → Resources → Add → Volume

Mount Path: /data
Size: 5GB (기본값)

이 경로에 SQLite DB가 저장됨:
/data/paper_company.db
```

**중요: 코드에서 Volume 경로 확인**

```python
# paper_company/db.py
DB_PATH = Path("/data/paper_company.db")
```

현재 코드를 확인해야 함. 기본값이 상대경로면 수정 필요.

### 5. 시작 명령 설정

Railway 프로젝트 → Settings → Start Command

```bash
# Option A: 모든 서비스 동시 실행 (간단함)
python scripts/local_runner.py & python scripts/paperclip_server.py & python scripts/telegram_poll.py & wait

# Option B: Procfile 사용 (권장)
Procfile 생성:
```

**Procfile (프로젝트 루트)**
```
runner: python scripts/local_runner.py
ui: python scripts/paperclip_server.py
telegram: python scripts/telegram_poll.py
```

Railway가 Procfile을 자동 감지.

### 6. Cron Job 설정 (7AM 매일 Morning Signal)

```bash
Railway 프로젝트 → Cron Jobs → Create Job

Name: paper-company-daily
Schedule: 0 7 * * * (7AM UTC)
Command: python scripts/explore_daily.py
```

**시간대 주의:**
- Railway Cron = UTC 기준
- 한국 시간 7AM = UTC 10PM (전날)
- 맞추려면: `0 22 * * *` (전날 밤 10시)

더블 체크: 원하는 시간이 뭔지 명확히 하자.

### 7. 배포 확인

```bash
Railway 프로젝트 → Deployments

최신 배포 상태 확인
- Building... → Complete ✓
- Deployed ✓

로그 확인:
- Logs 탭에서 실시간 로그 확인
```

---

## 테스트

### Telegram 테스트

```
/ping   → "pong from Paper Company"
/today  → Morning Signal 반환
/run    → 새로운 Signal 생성 (2-3분)
```

### HTTP 서버 테스트

```bash
# runner 헬스체크
curl https://<railway-domain>:8711/health

# Paperclip UI
https://<railway-domain>:8720
```

Railway가 자동으로 도메인 할당함.

---

## Procfile 해석

```
runner: python scripts/local_runner.py
│       │
│       └─ 실행 명령어
└─ 프로세스 이름 (Railway가 이를 별도 서비스로 관리)

ui: python scripts/paperclip_server.py
telegram: python scripts/telegram_poll.py
```

각 라인은 **병렬로 실행됨** (동시에 3개 서비스 실행).

---

## 주의사항

### 1. SQLite DB 경로 확인

현재 코드:
```python
# paper_company/db.py 확인
DB_PATH = Path("data/paper_company.db")  # 상대경로
```

이를 절대경로로 수정 필요:
```python
DB_PATH = Path("/data/paper_company.db")  # Railway Volume 경로
```

또는 환경변수로 유연하게:
```python
DB_PATH = Path(os.getenv("DB_PATH", "/data/paper_company.db"))
```

### 2. 포트 설정

Railway는 자동으로 포트를 할당. 코드에서 포트 hardcoding 피하기:
```python
# ❌ 나쁜 예
app.run(port=8711)

# ✅ 좋은 예
port = int(os.getenv("PORT", 8711))
app.run(port=port)
```

### 3. 크론 타이밍

7AM KST = 10PM UTC (전날)

Cron 설정:
```bash
0 22 * * *   # 전날 밤 10시 (UTC)
```

또는 정오(UTC):
```bash
0 12 * * *   # 오전 9시 KST
```

원하는 시간을 명확히 정하고 설정할 것.

---

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| Deployment 실패 | requirements.txt 의존성 오류 | `pip freeze` 실행 후 확인 |
| `/ping` 응답 없음 | telegram 프로세스 미실행 | Logs 탭에서 오류 확인 |
| Morning Signal 안 만들어짐 | Cron job 실패 또는 DB 경로 오류 | Cron Logs 확인, DB_PATH 수정 |
| DB 데이터 손실 | Volume 미설정 | Resources → Volume 추가 재확인 |

---

## Claude 인증 정보

Railway 환경에서도 `.claude` 필요:

### 방법 1: 시크릿으로 저장

```bash
# 로컬에서 ~/.claude 디렉터리를 secrets로 등록
# (복잡함)
```

### 방법 2: 환경 변수로 관리

```bash
# Railway Variables에 추가
CLAUDE_API_KEY=<your-api-key>

# 코드에서 사용
import os
os.environ["ANTHROPIC_API_KEY"] = os.getenv("CLAUDE_API_KEY")
```

현재 코드가 `~/.claude`에 의존하면 수정 필요.

---

## 비용

```
Hobby Plan: $5/month
- 0.5GB RAM, 1vCPU (충분함)
- SQLite 5GB Volume
- Cron job 포함

사용 예상:
- Bot 24/7: ~$0.30-0.50/month
- Cron job: 무료 (포함)
- Total: ~$5/month (Hobby plan 범위 내)
```

---

## GitHub Auto-Deploy

코드를 push하면 자동 배포:

```bash
git add .
git commit -m "..."
git push origin main
```

Railway가 GitHub webhook으로 감지 → 자동 빌드 & 배포.

**Procfile, requirements.txt, .env 설정 변경 후 푸시하면:**
- 새 빌드 시작
- 기존 프로세스 종료
- 새 버전 실행 (무중단 배포)

---

## 다음 단계

1. DB 경로 확인 & 수정 (`/data/paper_company.db`)
2. Procfile 생성 (프로젝트 루트)
3. requirements.txt 최신화
4. GitHub push
5. Railway 대시보드에서 배포 확인
6. Cron job 시간 설정 (7AM KST?)
7. Telegram 테스트

준비됐으면 시작하자!
