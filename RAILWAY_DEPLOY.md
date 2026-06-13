# Railway 배포 (한 줄 명령어)

## 🚀 빠른 배포 (3단계)

### 1️⃣ 로컬 준비

```bash
cd ~/Documents/GitHub/paper-company
bash scripts/railway-deploy.sh
```

이 스크립트가 자동으로:
- `requirements.txt` 최신화
- `Procfile` 생성
- `.env.railway.example` 생성
- 환경변수 체크리스트 출력

### 2️⃣ 변경사항 커밋 & Push

```bash
git add .
git commit -m "Railway 배포 준비"
git push origin main
```

### 3️⃣ Railway 대시보드 설정

#### A. 환경변수 설정
```
cloud.railway.app
→ 프로젝트 선택
→ Variables 탭

다음 변수들 입력:

TELEGRAM_BOT_TOKEN = (BotFather에서 발급)
DB_PATH = /data/paper_company.db
```

#### B. Volume 추가
```
Resources 탭
→ Add (+ 버튼)
→ Volume

Mount Path: /data
Size: 5GB (기본값)
```

#### C. Cron Job 설정
```
Cron Jobs 탭
→ Create New

Name: paper-company-daily
Schedule: 0 22 * * *  (7AM KST = 전날 밤 10시 UTC)
Command: python scripts/explore_daily.py
```

---

## 배포 상태 확인

```bash
cloud.railway.app → Deployments 탭

상태:
- Building... → Complete ✓
- Running ✓
```

## 로그 확인

```bash
cloud.railway.app → Logs 탭

실시간 로그 확인:
- runner: local_runner.py 출력
- ui: paperclip_server.py 출력
- telegram: telegram_poll.py 출력
```

## 테스트

### Telegram 확인
```
/ping   → "pong from Paper Company" ✓
/today  → Morning Signal ✓
/run    → 새 Signal 생성 (2-3분) ✓
```

### HTTP 확인
```bash
curl https://<railway-domain>/health
```

---

## 문제 해결

### Deployment 실패
```bash
Logs 탭에서 오류 확인
- ModuleNotFoundError → requirements.txt 수정
- DB 경로 오류 → DB_PATH 환경변수 확인
```

### Bot 응답 없음
```bash
Logs 탭 → telegram 프로세스 확인
- "Telegram bot polling started" 있는지 확인
- TELEGRAM_BOT_TOKEN 설정 확인
```

### Cron Job 실행 안 됨
```bash
Cron Jobs 탭 → 최근 실행 로그 확인
- 시간대 맞는지 확인 (UTC vs KST)
- Command 문법 확인
```

---

## 파일 구조

```
paper-company/
├── Procfile                    ← Railway이 읽음
├── requirements.txt            ← 의존성
├── .railway.env.example        ← Railway 환경변수 예시
├── scripts/
│   ├── railway-deploy.sh       ← 배포 준비 스크립트
│   ├── local_runner.py
│   ├── paperclip_server.py
│   ├── telegram_poll.py
│   └── explore_daily.py        ← Cron job이 실행
└── paper_company/
    ├── db.py                   ← DB_PATH 환경변수 지원
    └── ...
```

---

## 배포 후 코드 수정

코드를 수정하고 push하면 자동 배포:

```bash
# 코드 수정
vim paper_company/something.py

# 커밋 & 푸시
git add .
git commit -m "Fix: something"
git push origin main

# Railway가 자동으로:
# 1. GitHub webhook 감지
# 2. 새 빌드 시작
# 3. Procfile 실행
# 4. 기존 서비스 종료 & 새 버전 시작
```

---

## 환경변수 추가/변경

Railway 대시보드에서 변수 추가/수정:

```
Variables 탭 → 수정 → Save

변경사항 자동 반영 (재배포 필요 없음)
```

하지만 코드에서 환경변수를 읽게끔 되어있어야 함:

```python
# 예: db.py
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "data" / "paper_company.db"))
```

---

## 비용

```
Hobby Plan: $5/month

포함:
- 0.5GB RAM
- 1vCPU
- SQLite 5GB Volume
- Cron job 포함

우리 사용량:
- Bot 24/7: ~$0.30-0.50/month
- Total: ~$5/month (Hobby plan 범위 내)

초과 시:
- Pro Plan: $20/month (더 많은 리소스)
```

---

## 유용한 명령어

### requirements.txt 업데이트 (새 패키지 추가 후)
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### 로컬에서 Railway 환경 시뮬레이션
```bash
export DB_PATH=/tmp/test.db
export TELEGRAM_BOT_TOKEN=test-token
python scripts/explore_daily.py
```

### Cron 시간대 변환
```
KST 7AM = UTC 10PM (전날)
KST 12PM (정오) = UTC 3AM
KST 8PM = UTC 11AM

Cron 설정:
0 22 * * *   # 7AM KST
0 3 * * *    # 12PM KST
0 11 * * *   # 8PM KST
```

---

## 정리

1. `bash scripts/railway-deploy.sh` 실행
2. `git push origin main`
3. Railway 대시보드: Variables + Volume + Cron 설정
4. Telegram 테스트 ✓

완료!
