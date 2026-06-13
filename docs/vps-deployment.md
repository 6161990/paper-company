# VPS 배포 (Naver Cloud)

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ Naver Cloud VPS (Seoul)                             │
│ Ubuntu 22.04, 2vCPU, 4GB RAM, 50GB SSD              │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ systemd services (자동 시작 & 스케줄)         │ │
│ │                                                │ │
│ │ 1. paper-company-runner (:8711)               │ │
│ │    - Telegram /run 명령 처리                  │ │
│ │                                                │ │
│ │ 2. paper-company-telegram                      │ │
│ │    - Telegram polling (메시지 수신)           │ │
│ │                                                │ │
│ │ 3. paperclip (:8720)                          │ │
│ │    - Paperclip UI (SSH 터널로만 접근)         │ │
│ │                                                │ │
│ │ 4. paper-company-daily.timer                   │ │
│ │    - 매일 7AM KST → explore_daily.py 자동실행│ │
│ │    - Morning Signal 생성 & SQLite 저장        │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ Python 3.11                                         │
│ SQLite DB (/opt/paper-company/data/)                │
└─────────────────────────────────────────────────────┘
         ↑
         │ SSH (포트 22)
         │ 
  MacBook Local
  
         ↑↓
    Telegram API
    (/ping, /today, /run)
```

## 배포 흐름

### Why VPC/Subnet/Network ACL?

```
인터넷 ──→ 공인 IP:22 ──→ Network ACL ──→ Subnet ──→ Server
                        (방화벽)      (격리)    (실제 머신)
```

**VPC (Virtual Private Cloud) — IP 범위: 10.0.0.0/16**

- 클라우드에서 격리된 네트워크 공간
- **왜 10.0.0.0/16?**
  - `10.0.0.0/16` = 10.0.0.0 ~ 10.0.255.255 (65,536개 IP)
  - Private IP 범위 표준 (RFC 1918)
  - 일반적인 기업/클라우드 관례
  - 더 큰 범위를 예약해서 나중에 Subnet 여러 개 추가 가능
    - Subnet 1: 10.0.1.0/24 (256개)
    - Subnet 2: 10.0.2.0/24 (256개)
    - ... 계속 추가 가능

**Subnet — IP 범위: 10.0.1.0/24**

- VPC 안의 세부 네트워크
- **왜 10.0.1.0/24?**
  - `10.0.1.0/24` = 10.0.1.0 ~ 10.0.1.255 (256개 IP)
  - Server 1개만 필요하므로 /24로 충분 (254개 사용 가능)
  - VPC의 10.0.0.0/16 범위 **안에** 포함됨
  - Server는 10.0.1.10, 10.0.1.11 등의 IP를 할당받음

**Network ACL — IP 범위: 10.0.0.0/8**

- 네트워크 방화벽 (어떤 포트/IP를 허용할지)
- **왜 10.0.0.0/8?**
  - `10.0.0.0/8` = 10.0.0.0 ~ 10.255.255.255 (16,777,216개 IP)
  - Private IP 전체 범위
  - VPC 내부 통신은 모두 허용 (10.0.0.0/16도 포함)
  - 추후 VPC를 확장하거나 다른 네트워크와 연결할 때도 대비
  - SSH(22)는 모두 허용, Outbound도 모두 허용

**IP 범위 계층 관계:**

```
ACL 범위      10.0.0.0/8 (전체 private IP 허용)
  └─ VPC 범위    10.0.0.0/16 (VPC 격리)
      └─ Subnet 범위  10.0.1.0/24 (실제 Server가 들어갈 공간)
          └─ Server IP     10.0.1.10 (구체적 IP 할당)
```

---

## 배포 단계

### 1. VPC 생성

```bash
Naver Cloud 콘솔 → Networking → VPC → VPC 생성

VPC 이름: paper-vpc
IP 범위: 10.0.0.0/16
유형: NORMAL
```

### 2. Network ACL 생성

```bash
Networking → VPC → (paper-vpc 선택) → Network ACL → 생성

이름: paper-acl
유형: NORMAL
IP 범위: 10.0.0.0/8
```

### 3. Subnet 생성

```bash
Networking → VPC → (paper-vpc 선택) → Subnet → 생성

이름: paper-subnet
VPC: paper-vpc
IP 범위: 10.0.1.0/24
가용성 영역: KR-1 (Seoul)
```

### 4. Server 생성

```bash
Compute → Server → 생성

이미지: Ubuntu 22.04 LTS
서버 타입: 표준 (2vCPU, 4GB RAM, 50GB SSD)
지역: Korea (Seoul)
VPC: paper-vpc
Subnet: paper-subnet
공인 IP: 자동 할당
```

→ 2-3분 후 상태 "Running" 확인 → **공인 IP 메모**

---

## 배포 명령어

### SSH 접속

```bash
ssh -i ~/.ssh/naver_key root@PUBLIC_IP
```

### 패키지 & 사용자 설정

```bash
apt update && apt install -y git python3 python3-venv
useradd -m -s /bin/bash paper
```

### 코드 체크아웃

```bash
sudo -iu paper
git clone https://github.com/6161990/paper-company.git /opt/paper-company
cd /opt/paper-company
```

### Python 환경 & 의존성

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 환경 변수 설정

```bash
cp .env.example .env
nano .env
# TELEGRAM_BOT_TOKEN 입력 (BotFather에서 발급)
# 저장: Ctrl+X → Y → Enter
```

### Claude 인증 정보 복사

```bash
# 로컬 맥에서
scp -r -i ~/.ssh/naver_key ~/.claude paper@PUBLIC_IP:/home/paper/
```

### 수동 1회 테스트 (VPS에서)

```bash
cd /opt/paper-company
.venv/bin/python scripts/explore_daily.py
# 1-2분 소요 → data/briefs/2026-06-13.md 생성 확인
```

### systemd 서비스 등록

```bash
# paper 사용자에서 exit
exit

# 서비스 파일 복사 & 활성화
sudo cp /opt/paper-company/deploy/systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paper-company-runner paper-company-telegram paperclip
sudo systemctl enable --now paper-company-daily.timer
```

### 검증

```bash
systemctl list-timers | grep paper-company
# → 다음 7AM 시각 표시

systemctl status paper-company-runner
curl http://127.0.0.1:8711/health
```

---

## 테스트

### Telegram 확인

```
/ping   → "pong from Paper Company"
/today  → Morning Signal 반환
/run    → 새로운 Signal 생성 (2-3분)
```

### Paperclip UI 접근

```bash
# 로컬 맥에서
ssh -i ~/.ssh/naver_key -L 8720:127.0.0.1:8720 paper@PUBLIC_IP

# 브라우저: http://127.0.0.1:8720
```

---

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| SSH 접속 실패 | Network ACL 미설정 | VPC → Network ACL 생성 |
| explore_daily.py 오류 | ~/.claude 복사 실패 | `scp -r ~/.claude` 재실행 |
| 매일 7AM 실행 안 됨 | timer 미활성화 | `sudo systemctl enable paper-company-daily.timer` |

---

## systemd 타이머 작동 원리

```
매일 00:00 (자정) ──→ systemd 체크 ──→ 7AM 매칭?
                    
                    Yes ──→ paper-company-daily.service 실행
                           (explore_daily.py 호출)
                           ↓
                           Morning Signal 생성
                           SQLite 저장
                           Telegram 대기 중인 사용자가
                           /today 명령하면 반영됨
```

---

