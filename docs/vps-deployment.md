# VPS Deployment

목표:

```text
노트북이 꺼져 있어도
VPS에서 n8n이 오전 7시에 실행되고
Claude Agent SDK가 Morning Signal을 만들고
Telegram으로 전송하고
Paperclip에서 상태를 본다.
```

## Recommended First Deployment

초기에는 Paperclip을 공개 인터넷에 열지 않는다.

```text
Public:
  n8n : http://SERVER_IP:5678

Private:
  runner   : http://127.0.0.1:8711
  Paperclip: http://127.0.0.1:8720
  SQLite   : /opt/paper-company/data/paper_company.db
```

Paperclip은 SSH 터널로 본다.

```bash
ssh -L 8720:127.0.0.1:8720 paper@SERVER_IP
```

로컬 브라우저:

```text
http://127.0.0.1:8720
```

## Server Setup

Ubuntu 기준.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv docker.io docker-compose-plugin
sudo useradd -m -s /bin/bash paper
sudo usermod -aG docker paper
```

repo 위치:

```bash
sudo mkdir -p /opt
sudo chown paper:paper /opt
sudo -iu paper
cd /opt
git clone REPO_URL paper-company
cd paper-company
```

Python:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

환경변수:

```bash
cp .env.example .env
nano .env
```

필수:

```text
GENERIC_TIMEZONE=Asia/Seoul
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=SERVER_IP
TELEGRAM_BOT_TOKEN=...
```

## Claude Auth

VPS는 새 컴퓨터이므로 Claude 인증을 한 번 해야 한다.

```bash
.venv/bin/claude
```

Claude CLI 안에서:

```text
/login
```

표시되는 URL을 로컬 브라우저에서 열고 로그인한다.

확인:

```bash
.venv/bin/python scripts/explore_daily.py
```

성공하면 `data/briefs/YYYY-MM-DD.md`와 SQLite record가 생성된다.

## n8n

```bash
docker compose up -d
```

브라우저:

```text
http://SERVER_IP:5678
```

n8n workflow:

```text
Schedule Trigger
  -> HTTP Request
```

Schedule:

```text
Every day
07:00
Timezone: Asia/Seoul
```

HTTP Request:

```text
Method: POST
URL: http://host.docker.internal:8711/run/explore
Response Format: JSON
```

## systemd Services

root 계정으로:

```bash
sudo cp /opt/paper-company/deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paper-company-runner
sudo systemctl enable --now paperclip
sudo systemctl enable --now paper-company-telegram
```

상태 확인:

```bash
systemctl status paper-company-runner
systemctl status paperclip
systemctl status paper-company-telegram
```

로그:

```bash
journalctl -u paper-company-runner -f
journalctl -u paperclip -f
journalctl -u paper-company-telegram -f
```

## Verify

runner:

```bash
curl http://127.0.0.1:8711/health
```

Paperclip:

```bash
curl http://127.0.0.1:8720/health
```

Telegram:

```text
/ping
/today
```

## Today Delivery

배포 당일 바로 받으려면:

```text
1. Claude auth 완료
2. runner systemd 실행
3. Telegram bot systemd 실행
4. Telegram에서 /run 전송
```

오전 7시 자동 실행은 n8n Schedule Trigger까지 만든 뒤 다음 7시에 돈다.
