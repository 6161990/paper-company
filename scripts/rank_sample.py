import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.prompts import RANKING_PROMPT

CANDIDATES_PATH = ROOT / "paper_company" / "sample_candidates.json"


async def main() -> None:
    candidates = json.loads(CANDIDATES_PATH.read_text())
    prompt = f"{RANKING_PROMPT}\n\nCandidates:\n{json.dumps(candidates, ensure_ascii=False, indent=2)}"

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except ImportError:
        print("claude-agent-sdk is not installed yet.")
        print("Install later with: pip install claude-agent-sdk")
        print("For the current Paper Company flow, prefer: python3 scripts/explore_daily.py")
        print("\nPrompt preview:\n")
        print(prompt)
        return

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=[],
        ),
    ):
        print(message)


if __name__ == "__main__":
    asyncio.run(main())
