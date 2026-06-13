#!/bin/bash
# Railway 배포 준비 스크립트

set -e

echo "🚀 Railway 배포 준비 시작"
echo ""

# 1. requirements.txt 최신화
echo "1️⃣  requirements.txt 최신화..."
pip freeze > requirements.txt
echo "✓ requirements.txt 생성됨"
echo ""

# 2. Procfile 확인/생성
echo "2️⃣  Procfile 생성..."
cat > Procfile << 'EOF'
runner: python scripts/local_runner.py
ui: python scripts/paperclip_server.py
telegram: python scripts/telegram_poll.py
EOF
echo "✓ Procfile 생성됨"
echo ""

# 3. .env 확인
echo "3️⃣  환경변수 확인..."
if [ -f .env ]; then
    echo "✓ .env 파일 존재"
    echo "  필수 변수:"
    echo "  - TELEGRAM_BOT_TOKEN (필수)"
    echo "  - TELEGRAM_CHAT_ID (선택)"
    echo "  - DB_PATH=/data (Railway는 자동 설정, 로컬은 생략)"
else
    echo "⚠️  .env 파일 없음 - cp .env.example .env 후 TELEGRAM_BOT_TOKEN 입력"
fi
echo ""

# 4. Railway 배포용 .env 샘플
echo "4️⃣  Railway용 환경변수 설정 예시..."
cat > .env.railway.example << 'EOF'
# Railway 배포용 환경변수
# railway.app Dashboard → Variables 에 이 값들을 설정하세요

TELEGRAM_BOT_TOKEN=<BotFather에서 발급받은 토큰>
TELEGRAM_CHAT_ID=<선택사항>
DB_PATH=/data/paper_company.db

# Claude API 인증 (아래 중 하나 필요)
# 옵션 1: ~/.claude 디렉터리 전체 (복잡)
# 옵션 2: ANTHROPIC_API_KEY 환경변수 (간단)
ANTHROPIC_API_KEY=<your-anthropic-api-key>
EOF
echo "✓ .env.railway.example 생성됨"
echo ""

# 5. Git 상태 확인
echo "5️⃣  Git 변경사항 확인..."
git status --short
echo ""

# 6. 배포 체크리스트
echo "📋 Railway 배포 체크리스트:"
echo "---"
echo "[ ] 1. TELEGRAM_BOT_TOKEN 을 Railway Variables에 설정"
echo "[ ] 2. DB_PATH=/data 를 Railway Variables에 설정"
echo "[ ] 3. Volume 추가: Mount Path /data, Size 5GB"
echo "[ ] 4. Cron Job: 0 22 * * * python scripts/explore_daily.py (7AM KST)"
echo "[ ] 5. GitHub push: git push origin main"
echo "[ ] 6. Railway 대시보드에서 배포 확인"
echo "[ ] 7. Telegram /ping 테스트"
echo ""

# 7. 다음 명령어
echo "✅ 다음 단계:"
echo "---"
echo "1. Railway Variables 설정:"
echo "   cloud.railway.app → 프로젝트 → Variables"
echo ""
echo "2. GitHub push:"
echo "   git add ."
echo "   git commit -m 'Railway 배포 준비'"
echo "   git push origin main"
echo ""
echo "3. Railway 대시보드 확인:"
echo "   Deployments 탭에서 상태 확인"
echo ""
