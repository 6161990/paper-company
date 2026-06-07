import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.prompts import DEEP_DIVE_PROMPT, get_agent_for_weekday
from paper_company.brief_parser import parse_brief_auto
from paper_company.db import replace_items, save_brief_record


INTERESTS_PATH = ROOT / "paper_company" / "interests.json"
FEEDBACK_PATH = ROOT / "paper_company" / "recent_feedback.json"
BRIEFS_DIR = ROOT / "data" / "briefs"
KST = ZoneInfo("Asia/Seoul")


def extract_text(message: object) -> str:
    result = getattr(message, "result", None)
    if isinstance(result, str) and result.strip():
        return result.strip()

    parts: list[str] = []
    for block in getattr(message, "content", []) or []:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def load_recent_briefs(limit: int = 5) -> str:
    if not BRIEFS_DIR.exists():
        return "최근 브리프 없음."

    current = today_kst()
    paths = sorted(BRIEFS_DIR.glob("*.md"), reverse=True)
    snippets: list[str] = []

    for path in paths:
        if path.stem == current:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        snippets.append(f"## {path.name}\n{text[:3500]}")
        if len(snippets) >= limit:
            break

    return "\n\n---\n\n".join(snippets) if snippets else "최근 브리프 없음."


def save_brief(text: str) -> tuple[Path, int]:
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    today = today_kst()
    path = BRIEFS_DIR / f"{today}.md"
    path.write_text(text + "\n", encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    brief_id = save_brief_record(
        run_date=today,
        title=f"Morning Signal - {today}",
        content=text,
        markdown_path=path,
        content_hash=digest,
    )
    replace_items(brief_id, parse_brief_auto(text))
    return path, brief_id


def get_today_weekday() -> int:
    return datetime.now(KST).weekday()


def build_prompt(interests: dict, feedback: dict, recent_briefs: str) -> str:
    weekday = get_today_weekday()
    agent = get_agent_for_weekday(weekday)

    prompt = DEEP_DIVE_PROMPT.format(
        agent_name=agent["name"],
        agent_description=agent["description"],
    )

    prompt += f"""

오늘의 Deep Dive를 만들기 위해 웹을 탐색해라.

사용자 프로필:
{json.dumps(interests, ensure_ascii=False, indent=2)}

최근 피드백:
{json.dumps(feedback, ensure_ascii=False, indent=2)}

최근 Morning Signal이다. 아래와 같은 핵심 주제, 출처, angle은 반복하지 마라:
{recent_briefs}

탐색 규칙:
- 반드시 한국어로 작성한다.
- DEEP DIVE는 반드시 1개만 선정한다.
- CANDIDATES는 3-5개 선정한다.
- 오늘 담당 에이전트({agent["name"]}) 관점을 우선하되, Free 에이전트일 때는 가장 강렬한 발견을 선택한다.
- 우선 확인 소스: {", ".join(agent.get("sources", []))}
- 각 아이템에 link(URL), description, 왜 더 파야 하는가, 다음 30분 액션을 반드시 포함한다.
- 출력은 반드시 위의 형식을 따른다 (## DEEP DIVE, ## CANDIDATES 헤더 포함).
"""
    return prompt


def print_progress(message: object) -> None:
    name = type(message).__name__
    subtype = getattr(message, "subtype", None)

    if name == "SystemMessage":
        print("[시작] Claude Agent SDK 세션이 열렸습니다.", flush=True)
        return

    if name == "AssistantMessage":
        content = getattr(message, "content", []) or []
        block_names = [type(block).__name__ for block in content]
        if any("ToolUse" in block_name for block_name in block_names):
            print("[탐색] 웹 도구를 사용하고 있습니다.", flush=True)
        elif extract_text(message):
            print("[작성] 발견한 내용을 정리하고 있습니다.", flush=True)
        else:
            print("[진행] Claude가 다음 탐색 방향을 판단하고 있습니다.", flush=True)
        return

    if name == "UserMessage":
        print("[도구] 웹 검색/페이지 읽기 결과를 받았습니다.", flush=True)
        return

    if name == "ResultMessage":
        if getattr(message, "is_error", False):
            print("[오류] 실행 중 문제가 발생했습니다.", flush=True)
        else:
            print("[완료] Morning Signal 생성이 끝났습니다.", flush=True)
        return

    if subtype:
        print(f"[진행] {name}:{subtype}", flush=True)
    else:
        print(f"[진행] {name}", flush=True)


async def main() -> None:
    weekday = get_today_weekday()
    agent = get_agent_for_weekday(weekday)

    interests = json.loads(INTERESTS_PATH.read_text())
    feedback = json.loads(FEEDBACK_PATH.read_text())
    recent_briefs = load_recent_briefs()

    prompt = build_prompt(interests, feedback, recent_briefs)

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except ImportError:
        print("claude-agent-sdk is not installed yet.")
        print("Install later with: pip install claude-agent-sdk")
        print("\nExploration prompt preview:\n")
        print(prompt)
        return

    messages: list[str] = []
    print(f"Paper Company 탐색을 시작합니다. (담당: {agent['name']} Agent)", flush=True)

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["WebSearch", "WebFetch"],
            ),
        ):
            print_progress(message)
            text = extract_text(message)
            if text:
                messages.append(text)
    except Exception as exc:
        message = str(exc)
        if (
            "Not logged in" in message
            or "/login" in message
            or "Claude Code returned an error result" in message
        ):
            print("Claude Agent SDK is installed, but Claude Code is not authenticated.")
            print("Run `claude` in a terminal, then run `/login`.")
            print("After login, retry: .venv/bin/python scripts/explore_daily.py")
            return
        raise

    if not messages:
        print("Claude Agent SDK completed, but no brief text was returned.")
        return

    brief = messages[-1]
    path, brief_id = save_brief(brief)
    print("\n--- Morning Signal ---\n")
    print(brief)
    print(f"\nSaved Morning Signal: {path}")
    print(f"Saved SQLite brief_id: {brief_id}")


if __name__ == "__main__":
    asyncio.run(main())
