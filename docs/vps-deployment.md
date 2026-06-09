# VPS 배포 가이드

## 목표
맥북이 꺼져 있어도 매일 오전 7시 KST에 Morning Signal이 자동 생성되고 Telegram으로 전송되어야 한다.

## 권장 VPS 서버

### Option A: Oracle Cloud Free Tier (권장 - $0)
- 스펙: 4 ARM OCPU + 24GB RAM + 200GB SSD
- 프로비저닝: Frankfurt 또는 Singapore 지역 추천 (용량 여유 있음)
- 비용: 영구 무료
- 단점: 프로비저닝 시 "out of capacity" 오류로 1-3일 소요 가능

### Option B: Hetzner CX22 (대안 - $4.70/mo)
- 스펙: 2vCPU + 4GB RAM + 40GB NVMe
- 프로비저닝: 즉시 (클릭 후 5분 내 준비)
- 비용: ~€4.35/mo
- 장점: 빠른 배포, 안정적

### Option C: AWS Lightsail
- 스펙: 2vCPU + 2GB RAM + 60GB SSD ($12/mo)
- 비용: Hetzner보다 비쌈
- 장점: AWS 익숙한 사용자용

## 아키텍처

```
Local:
  - Python 3.11 앱
  - Claude Agent SDK (Claude 인증 필요)
  - SQLite DB

VPS (systemd services):
  - paper-company-runner (포트 8711) ← Telegram /run 명령 처리
  - paper-company-telegram            ← Telegram polling
  - paperclip (포트 8720)             ← SSH 터널로만 접근

Scheduled:
  - systemd timer (매일 7AM KST)
    → paper-company-daily.service
    → explore_daily.py 직접 실행 (Docker 불필요)
```

## 배포 단계

### 1. VPS 인스턴스 생성

**Oracle Cloud Free 콘솔:**
- Compute → Instances → Create Instance
- Image: Canonical Ubuntu 22.04
- Shape: Compute → Always Free (VM.Standard.A1.Flex)
- Network: VCN 기본값, Public IP 자동 할당
- 생성 후 `ssh -i key.pem ubuntu@PUBLIC_IP`

**Hetzner 콘솔:**
- Cloud Console → Servers → Create Server
- Image: Ubuntu 22.04
- Type: CX22
- Datacenter: 아무거나 (모두 빠름)
- SSH key 등록
- 생성 후 `ssh -i key.pem root@PUBLIC_IP`

### 2. 초기 설정

```bash
# Oracle: ubuntu 사용자, Hetzner: root 사용자
sudo apt update
sudo apt install -y git python3 python3-venv

# 전용 사용자 생성
sudo useradd -m -s /bin/bash paper
sudo usermod -aG docker paper  # (필요하면 Docker 설치하고 추가)
```

### 3. 코드 체크아웃

```bash
sudo -iu paper
mkdir -p /opt
git clone https://github.com/6161990/paper-company.git /opt/paper-company
cd /opt/paper-company

# Python 환경 설정
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
nano .env
# 필수: TELEGRAM_BOT_TOKEN (BotFather에서 발급)
# 선택: TELEGRAM_CHAT_ID
```

### 4. Claude Agent SDK 인증

**로컬 맥에서 미리 인증 정보 준비:**

Claude Code에서 이미 로그인했다면 `~/.claude` 디렉터리에 인증 정보가 저장되어 있다.

```bash
# 로컬 맥에서 확인
ls ~/.claude
```

**VPS에 인증 정보 복사:**

```bash
# 로컬 맥에서
scp -r ~/.claude paper@SERVER_IP:/home/paper/

# VPS에서 (이미 인증됨)
cd /opt/paper-company
.venv/bin/python scripts/explore_daily.py
# Claude Agent SDK가 ~/.claude의 인증 정보 자동 사용
```

로컬에서 인증이 안 됐다면, Claude Code 웹앱(claude.ai/code)에 한 번 로그인 하면 자동으로 `~/.claude`가 생성된다.

### 5. systemd 서비스 등록

```bash
# 서비스 파일 복사
sudo cp /opt/paper-company/deploy/systemd/*.service /etc/systemd/system/
sudo cp /opt/paper-company/deploy/systemd/*.timer /etc/systemd/system/

# systemd 재로드
sudo systemctl daemon-reload

# 3개 서비스 활성화 (start 포함)
sudo systemctl enable --now paper-company-runner
sudo systemctl enable --now paper-company-telegram
sudo systemctl enable --now paperclip

# 매일 7AM 타이머 활성화
sudo systemctl enable --now paper-company-daily.timer
```

### 6. 검증

```bash
# 서비스 상태 확인
systemctl status paper-company-runner
systemctl status paper-company-telegram
systemctl status paperclip

# 다음 Morning Signal 실행 시각 확인
systemctl list-timers | grep paper-company

# runner 헬스체크
curl http://127.0.0.1:8711/health

# 로그 확인
journalctl -u paper-company-runner -f
journalctl -u paper-company-telegram -f
journalctl -u paper-company-daily -f
```

### 7. 수동 1회 실행 테스트

```bash
# 스케줄 대기 없이 지금 바로 실행
sudo systemctl start paper-company-daily.service

# 로그 실시간 확인
journalctl -u paper-company-daily -f
```

완료되면 `SIGTERM`으로 종료.

### 8. Telegram으로 확인

```
/ping   → "pong from Paper Company" 응답
/today  → 최신 Morning Signal 반환
/run    → 새 Morning Signal 생성 (2-3분 소요)
```

### 9. Paperclip UI 접근 (SSH 터널)

Paperclip UI는 로컬 개발 목적이므로 공개 인터넷에 노출하지 않는다.
SSH 터널로만 접근:

```bash
# 로컬 머신에서
ssh -L 8720:127.0.0.1:8720 paper@SERVER_IP

# 로컬 브라우저: http://127.0.0.1:8720
```

## 문제해결

### "TELEGRAM_BOT_TOKEN is missing"
→ `.env` 파일 확인, BotFather에서 새 토큰 발급, `/opt/paper-company/.env`에 입력

### "/login 후 Claude 명령이 안 먹음"
→ `claude` CLI가 인증 정보를 찾지 못함
```bash
# 다시 로그인
.venv/bin/claude
/login
```

### "systemctl enable --now 후에도 서비스 안 떠있음"
```bash
# 상태 확인
systemctl status paper-company-runner

# 로그 확인
journalctl -u paper-company-runner -n 50

# 수동 시작 + 로그 보기
sudo systemctl start paper-company-runner
journalctl -u paper-company-runner -f
```

### "systemd timer가 7시에 안 돈다"
```bash
# 다음 실행 시각 확인
systemctl list-timers paper-company-daily

# 수동으로 1회 테스트
sudo systemctl start paper-company-daily.service
journalctl -u paper-company-daily -f
```

## 메모

- n8n은 설치하지 않는다 (Docker 불필요)
- systemd timer + `explore_daily.py` 직접 실행으로 충분
- SSH 터널을 통해 Paperclip 접근 (보안)
- 매일 7AM KST에 자동 실행 (Persistent=true로 설정됨)
