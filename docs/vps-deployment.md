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

### CIDR이 뭔가?

**CIDR (Classless Inter-Domain Routing)** = IP 주소 범위 표기법

```
10.0.0.0/16

├─ 10.0.0.0     = IP 주소
└─ /16          = 앞 16비트는 "고정", 뒤 16비트는 "가변"

IP는 32비트 (4개 구간 × 8비트)
┌─────────┬─────────┬─────────┬─────────┐
│ 00001010│ 00000000│ 00000000│ 00000000│  = 10.0.0.0
│   10    │    0    │    0    │    0    │  (10진법)
└─────────┴─────────┴─────────┴─────────┘
         8비트      8비트      8비트      8비트

/16 = 앞 16비트 고정 (10.0 부분)
      뒤 16비트 가변 (0.0 ~ 255.255)
      
결과: 10.0.0.0 ~ 10.0.255.255 (65,536개 IP)
```

---

### IP 범위 도형 설명

**1단계: ACL (방화벽 범위) — 10.0.0.0/8**

```
10.0.0.0/8 (앞 8비트 고정 = "10" 부분만 고정)

┌────────────────────────────────────────────────┐
│                  전체 Private IP                │
│            10.0.0.0 ~ 10.255.255.255            │
│                 (16,777,216개 IP)              │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  VPC (10.0.0.0/16)                      │ │
│  │  10.0.0.0 ~ 10.0.255.255                │ │
│  │  (65,536개 IP)                          │ │
│  │                                          │ │
│  │  ┌────────────────────────────────────┐ │ │
│  │  │ Subnet (10.0.1.0/24)               │ │ │
│  │  │ 10.0.1.0 ~ 10.0.1.255             │ │ │
│  │  │ (256개 IP)                         │ │ │
│  │  │                                    │ │ │
│  │  │ Server: 10.0.1.10 ← 실제 머신   │ │ │
│  │  └────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘

ACL 역할: 이 전체 영역의 통신을 제어
VPC 역할: 10.0.x.x 영역만 격리
Subnet 역할: 10.0.1.x 영역에만 Server 배치
```

---

**2단계: /숫자가 뭔가? (비트 관점)**

```
/숫자 = 앞 N비트는 고정, 뒤는 자유

비트 구조 (IP = 32비트 = 4 × 8비트)

10.0.0.0/8 (앞 8비트 고정 = 첫 번째 구간만 고정)
┌─────────┬─────────┬─────────┬─────────┐
│  고정   │  자유   │  자유   │  자유   │
│   10    │ 0~255  │ 0~255  │ 0~255  │
│ (8비트) │(8비트) │(8비트) │(8비트) │
└─────────┴─────────┴─────────┴─────────┘
  가변 범위: 10.0.0.0 ~ 10.255.255.255


10.0.0.0/16 (앞 16비트 고정 = 첫 두 구간 고정)
┌─────────┬─────────┬─────────┬─────────┐
│  고정   │  고정   │  자유   │  자유   │
│   10    │    0    │ 0~255  │ 0~255  │
│(8비트)  │(8비트)  │(8비트) │(8비트) │
└─────────┴─────────┴─────────┴─────────┘
  가변 범위: 10.0.0.0 ~ 10.0.255.255


10.0.1.0/24 (앞 24비트 고정 = 첫 세 구간 고정)
┌─────────┬─────────┬─────────┬─────────┐
│  고정   │  고정   │  고정   │  자유   │
│   10    │    0    │    1    │ 0~255  │
│(8비트)  │(8비트)  │(8비트) │(8비트) │
└─────────┴─────────┴─────────┴─────────┘
  가변 범위: 10.0.1.0 ~ 10.0.1.255
```

---

**3단계: 왜 /24, /16, /8을 선택했나?**

```
필요한 IP 개수 ──→ 적절한 /숫자 선택

Server 1개만 필요
├─ 1개 Server = 1개 IP 필요
├─ 하지만 여유를 봐서 256개 정도 예약
└─ /24 = 256개 ✓ (10.0.1.0 ~ 10.0.1.255)

Subnet 여러 개를 VPC 안에 만들 가능성
├─ Subnet 1: 10.0.1.0/24 (256개)
├─ Subnet 2: 10.0.2.0/24 (256개)
├─ Subnet 3: 10.0.3.0/24 (256개)
├─ ... 계속 추가 가능
└─ VPC는 /16 = 65,536개 ✓

방화벽(ACL)은 보수적으로
├─ VPC가 나중에 확장될 수 있음
├─ Private IP 전체 범위 허용해도 안전
└─ ACL은 /8 = 전체 private IP ✓
```

---

**4단계: 구체적 IP 할당**

```
VPC: 10.0.0.0/16
└─ Subnet: 10.0.1.0/24 에 Server 배치

Server가 받을 IP 예시:
┌────────────────────────┐
│ 10.0.1.1   (Gateway)  │
│ 10.0.1.2   (Reserved) │
│ 10.0.1.3   (Reserved) │
│ 10.0.1.4   (Reserved) │
│ 10.0.1.5               │ ← Server A
│ 10.0.1.6               │ ← Server B
│ 10.0.1.7               │ ← Server C
│ ...                    │
│ 10.0.1.254 (Broadcast)│
└────────────────────────┘
   (총 256개 = /24)
```

---

### Why VPC/Subnet/Network ACL?

```
인터넷 ──→ 공인 IP:22 ──→ Network ACL ──→ Subnet ──→ Server
                        (방화벽)      (격리)    (실제 머신)
```

**정리:**

| 계층 | CIDR | 크기 | 역할 |
|---|---|---|---|
| **Network ACL** | 10.0.0.0/**8** | 16.7M IP | 전체 private 범위 필터링 (보수적) |
| **VPC** | 10.0.0.0/**16** | 65K IP | 클라우드 격리 공간 (여러 Subnet 수용) |
| **Subnet** | 10.0.1.0/**24** | 256 IP | 실제 Server 배치 (1개만 필요) |
| **Server** | 10.0.1.10 | 1 IP | 실제 머신 |

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

