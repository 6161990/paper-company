# VPS 배포 가이드

## 목표
맥북이 꺼져 있어도 매일 오전 7시 KST에 Morning Signal이 자동 생성되고 Telegram으로 전송되어야 한다.

## 권장 VPS 서버

### Option A: Naver Cloud (권장 - 초기 무료)
- 스펙: 2vCPU + 4GB RAM + 50GB SSD
- 데이터센터: 한국 (서울)
- 비용: 초기 크레딧 받음 (3-6개월 무료), 이후 ~₩10,000/mo
- 장점: 한국 기업, 문의 한국어, 커뮤니티 많음
- 프로비저닝: 즉시

### Option B: Hetzner CX22 (국제 대안 - $4.70/mo)
- 스펙: 2vCPU + 4GB RAM + 40GB NVMe
- 데이터센터: 유럽 (지연 낮음)
- 비용: €4.35/mo (~$4.70)
- 장점: 빠른 배포, 안정적

### Option C: Oracle Cloud Free Tier ($0)
- 스펙: 4 ARM OCPU + 24GB RAM + 200GB SSD
- 비용: 영구 무료
- 단점: 프로비저닝 로또 (1-3일 대기 가능)

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

### 0. Network ACL 설정 (VPC 생성 후)

**Network ACL (Access Control List)** = 네트워크 방화벽

VPC 생성 직후 ACL을 설정해야 SSH 접속 가능:

**Naver Cloud 콘솔:**
1. **Networking → VPC**
2. 방금 만든 VPC 선택
3. **Network ACL** 탭 클릭
4. **Network ACL 생성**:
   - **이름**: `paper-acl` (아무거나)
   - **IP 주소 범위**: 기본값 (Private: 10.0.0.0/8)
   - **유형**: NORMAL
5. **생성** 클릭

**설정 화면:**
```
VPC 생성 창에서:
┌─────────────────────────┐
│ VPC 생성                │
│                         │
│ VPC 이름: paper-vpc    │
│ IP 주소 범위: 10.0.0.0/16 │
│ 유형: NORMAL           │
│ [생성]                 │
└─────────────────────────┘
```

이 단계가 완료되면 Subnet 생성 가능.

---

### 1. VPS 인스턴스 생성

**Naver Cloud 콘솔:**

1. **console.ncloud.com** 접속 (가입/로그인)
2. **Compute → Server**
3. **Server 생성** 클릭
4. 설정:
   - **이미지**: Ubuntu 22.04 LTS
   - **서버 타입**: 표준 (2vCPU, 4GB RAM, 50GB SSD)
   - **지역**: Korea (Seoul)
   - **VPC**: 방금 만든 VPC 선택
   - **Subnet**: 방금 만든 Subnet 선택
   - **공인 IP**: 자동 할당 ✓
5. **생성** 클릭 (2-3분 소요)

→ 서버 상태가 **"Running"**이 되면 **공인 IP** 메모.

**초기 크레딧 신청:**
- Naver Cloud 콘솔 → 우측 상단 → "크레딧/쿠폰" → 신규 가입자 크레딧 신청
- 승인되면 3-6개월 무료 사용

**SSH 로그인:**
```bash
ssh -i ~/.ssh/naver_key root@PUBLIC_IP
```

Naver Cloud는 root 사용자로 시작 (ubuntu 사용자 아님).

### 2. 초기 설정

```bash
# Naver Cloud: root 사용자
apt update
apt install -y git python3 python3-venv

# 전용 사용자 생성
useradd -m -s /bin/bash paper
```

### 3. 코드 체크아웃 & 환경 설정

```bash
sudo -iu paper
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
# 저장: Ctrl+X → Y → Enter
```

### 4. Claude Agent SDK 인증

**로컬 맥에서 인증 정보 복사:**

Claude Code에서 이미 로그인했다면 `~/.claude` 디렉터리에 인증 정보가 저장되어 있다.

```bash
# 로컬 맥에서
ls ~/.claude  # 디렉터리 확인

# VPS로 복사
scp -r -i ~/.ssh/naver_key ~/.claude paper@PUBLIC_IP:/home/paper/
```

**VPS에서 테스트:**

```bash
# VPS에서 (paper 사용자)
cd /opt/paper-company
.venv/bin/python scripts/explore_daily.py
# 1-2분 소요, Morning Signal 생성됨
```

완료되면 `data/briefs/2026-06-13.md` 파일이 생성되고 SQLite에 기록됨.

### 5. systemd 서비스 등록

```bash
# root로 전환
exit

# 서비스 파일 복사
sudo cp /opt/paper-company/deploy/systemd/* /etc/systemd/system/

# systemd 재로드
sudo systemctl daemon-reload

# 3개 서비스 활성화 (자동 시작)
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
# 로컬 맥에서
ssh -i ~/.ssh/naver_key -L 8720:127.0.0.1:8720 paper@PUBLIC_IP

# 로컬 브라우저: http://127.0.0.1:8720
```

## 문제해결

### "TELEGRAM_BOT_TOKEN is missing"
→ `.env` 파일 확인, BotFather에서 새 토큰 발급, `/opt/paper-company/.env`에 입력

### "explore_daily.py 실행 실패"
→ Claude Agent SDK 인증 정보 누락
```bash
# 로컬 맥에서 다시 복사
scp -r -i ~/.ssh/naver_key ~/.claude paper@PUBLIC_IP:/home/paper/

# VPS에서 재실행
.venv/bin/python scripts/explore_daily.py
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

## Naver Cloud 참고사항

- **공인 IP**: 서버를 중지해도 유지됨
- **방화벽**: 기본적으로 포트 22(SSH)만 열려있음. Telegram polling은 outbound만 필요 (문제 없음)
- **한글 지원**: 대시보드, 가이드, 고객지원 모두 한국어
- **크레딧**: 신규 가입자 크레딧 신청하면 3-6개월 무료 사용 가능
