import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.db import (
    finish_run,
    get_latest_brief,
    list_recent_feedback,
    save_feedback,
    save_mobile_request,
    start_run,
)


API_BASE = "https://api.telegram.org/bot"
FEEDBACK_PATH = ROOT / "paper_company" / "recent_feedback.json"


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def telegram_call(token: str, method: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = urllib.request.Request(f"{API_BASE}{token}/{method}", data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


TELEGRAM_MESSAGE_LIMIT = 3900


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        cut = remaining.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit

        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return chunks


def send_message(token: str, chat_id: int, text: str) -> None:
    telegram_call(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


def send_long_message(token: str, chat_id: int, text: str) -> None:
    chunks = split_message(text)
    for index, chunk in enumerate(chunks, start=1):
        prefix = f"[{index}/{len(chunks)}]\n" if len(chunks) > 1 else ""
        send_message(token, chat_id, prefix + chunk)


def command_name(text: str) -> str:
    first = text.strip().split(maxsplit=1)[0] if text.strip() else ""
    return first if first.startswith("/") else "message"


def command_body(text: str) -> str:
    parts = text.strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def format_deep_dive(content: str) -> str:
    """Markdown 파일을 Telegram 가독성있게 포맷팅"""
    lines = content.strip().split("\n")
    result = []
    in_action = False
    action_count = 0

    for line in lines:
        # ## DEEP DIVE 제목
        if line.startswith("## DEEP DIVE"):
            result.append("📍 *DEEP DIVE*")
            continue

        # ### 제목
        if line.startswith("### "):
            title = line.replace("### ", "").strip()
            result.append(f"\n*{title}*")
            continue

        # **category**
        if line.startswith("**category**"):
            category = line.replace("**category**", "").strip()
            emoji_map = {
                "AI": "🤖",
                "Backend": "⚙️",
                "Money": "💰",
                "Stock": "📈",
                "Business": "💼",
                "People": "👤",
            }
            emoji = next(
                (v for k, v in emoji_map.items() if k.lower() in category.lower()),
                "📌",
            )
            result.append(f"{emoji} {category}")
            continue

        # **link**
        if line.startswith("**link**"):
            url = line.replace("**link**", "").strip()
            result.append(f"🔗 [링크보기]({url})")
            continue

        # **description**
        if line.startswith("**description**"):
            desc = line.replace("**description**", "").strip()
            result.append(f"\n_{desc}_")
            continue

        # **왜 더 파야 하는가** 또는 **why**
        if "왜 더 파야" in line or "왜 파야" in line:
            why = line.split("**", 2)[-1].strip() if "**" in line else line
            result.append(f"\n💡 *왜?* {why}")
            in_action = False
            continue

        # **다음 30분 액션**
        if "30분 액션" in line or "30분 action" in line:
            result.append(f"\n⏱️ *30분 액션*")
            in_action = True
            action_count = 0
            continue

        # 액션 항목들 (1. 2. 3. 으로 시작)
        if in_action and line.strip() and (
            line.strip()[0].isdigit() and ". " in line
        ):
            action_text = line.strip().split(". ", 1)[1] if ". " in line else line
            action_count += 1
            result.append(f"{action_count}️⃣ {action_text}")
            continue

        # 빈 줄
        if not line.strip():
            continue

        # 다른 필드들 (hook, expansion 등)
        if line.startswith("**") and "**" in line[2:]:
            parts = line.split("**")
            if len(parts) >= 3:
                key = parts[1]
                value = parts[2].strip()
                if value:
                    result.append(f"• _{key}_: {value}")
            continue

    return "\n".join(result)


def latest_brief_text() -> str:
    brief = get_latest_brief()
    if brief is None:
        return "아직 저장된 Morning Signal이 없습니다. /run 으로 먼저 생성해줘."

    formatted = format_deep_dive(brief["content"])
    return f"✨ *{brief['title']}*\n\n{formatted}"


def run_exploration(token: str = None, chat_id: int = None) -> tuple[bool, str]:
    run_id = start_run(service="morning_signal", trigger_type="telegram_run")
    stdout_lines = []
    stderr_lines = []

    try:
        proc = subprocess.Popen(
            [str(ROOT / ".venv" / "bin" / "python"), "scripts/explore_daily.py"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Read output in real-time
        import select
        while True:
            ready = select.select([proc.stdout, proc.stderr], [], [], 0.1)

            for stream in ready[0]:
                line = stream.readline()
                if line:
                    line = line.rstrip()
                    if stream == proc.stdout:
                        stdout_lines.append(line)
                        print(f"[explore] {line}", flush=True)
                    else:
                        stderr_lines.append(line)
                        print(f"[explore-err] {line}", flush=True)

                    # Send to Telegram if available
                    if token and chat_id and "[완료]" in line:
                        send_message(token, chat_id, f"✅ {line}")

            if proc.poll() is not None:
                break

        proc.wait(timeout=1200)

    except subprocess.TimeoutExpired as exc:
        proc.kill()
        finish_run(
            run_id,
            status="timeout",
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            error="explore_daily.py timed out after 1200 seconds",
        )
        return False, "explore_daily.py timed out after 1200 seconds"

    finish_run(
        run_id,
        status="success" if proc.returncode == 0 else "error",
        returncode=proc.returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
    )
    if proc.returncode != 0:
        return False, "\n".join(stderr_lines) or "\n".join(stdout_lines) or "explore_daily.py failed"
    return True, latest_brief_text()


def refresh_recent_feedback_file() -> None:
    rows = list_recent_feedback(limit=20)
    payload = [
        {
            "type": row["feedback_type"],
            "note": row["note"],
            "brief_date": row["brief_date"],
            "item": row["item_title"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    FEEDBACK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def save_mobile_feedback(feedback_type: str, note: str) -> str:
    if not note:
        return f"내용이 비어 있습니다. 예: /{feedback_type} 오늘 주식/비즈니스 개념 좋았어"

    brief = get_latest_brief()
    brief_id = int(brief["id"]) if brief is not None else None
    feedback_id = save_feedback(
        feedback_type=feedback_type,
        note=note,
        brief_id=brief_id,
    )
    refresh_recent_feedback_file()
    return f"저장했습니다. feedback_id={feedback_id}"


def handle_text(text: str, token: str = None, chat_id: int = None) -> tuple[str, bool]:
    command = command_name(text)

    if command == "/ping":
        return "pong from Paper Company", False

    if command == "/today":
        return latest_brief_text(), True

    if command == "/run":
        ok, response = run_exploration(token, chat_id)
        if not ok:
            return f"Morning Signal 생성 실패:\n{response}", True
        return response, True

    if command == "/help":
        return "\n".join(
            [
                "Paper Company commands",
                "/ping - 연결 확인",
                "/today - 최신 Morning Signal 받기",
                "/run - 새 Morning Signal 생성 후 받기",
                "/save 내용 - 아이디어 저장",
                "/feedback 내용 - Morning Signal 피드백 저장",
                "/ask - 리서치 요청 예정",
            ]
        ), False

    if command == "/save":
        return save_mobile_feedback("save", command_body(text)), False

    if command == "/feedback":
        return save_mobile_feedback("feedback", command_body(text)), False

    if command == "/ask":
        return f"{command} 명령은 준비 중입니다. 지금은 요청만 기록했습니다.", False

    return "아직 지원하지 않는 메시지입니다. /help 를 보내면 가능한 명령을 볼 수 있습니다.", False


def poll(token: str) -> None:
    print("Paper Company Telegram bot polling started.")
    offset = 0

    while True:
        try:
            response = telegram_call(
                token,
                "getUpdates",
                {
                    "timeout": 30,
                    "offset": offset,
                    "allowed_updates": json.dumps(["message"]),
                },
            )
            for update in response.get("result", []):
                offset = max(offset, update["update_id"] + 1)
                message = update.get("message") or {}
                text = message.get("text") or ""
                chat = message.get("chat") or {}
                chat_id = chat.get("id")
                if chat_id is None or not text:
                    continue

                command = command_name(text)
                print(f"received {command} from chat {chat_id}", flush=True)
                if command == "/run":
                    send_message(token, chat_id, "Morning Signal 생성을 시작했습니다. 보통 몇 분 걸립니다.")

                reply, is_long = handle_text(text, token, chat_id)
                save_mobile_request(
                    command=command,
                    input_text=text,
                    response_text=reply,
                )
                if is_long:
                    send_long_message(token, chat_id, reply)
                else:
                    send_message(token, chat_id, reply)
                print(f"handled {command} from chat {chat_id}", flush=True)
        except KeyboardInterrupt:
            print("Telegram bot stopped.")
            return
        except Exception as exc:
            print(f"Telegram polling error: {exc}", file=sys.stderr)
            time.sleep(5)


def main() -> None:
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN is missing.")
        print("Create a bot with BotFather, then add TELEGRAM_BOT_TOKEN=... to .env")
        sys.exit(1)
    poll(token)


if __name__ == "__main__":
    main()
