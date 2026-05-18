import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.brief_parser import parse_brief_items
from paper_company.db import replace_items, save_brief_record


BRIEFS_DIR = ROOT / "data" / "briefs"


def main() -> None:
    for path in sorted(BRIEFS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        brief_id = save_brief_record(
            run_date=path.stem,
            title=f"Morning Signal - {path.stem}",
            content=content,
            markdown_path=path,
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )
        items = parse_brief_items(content)
        replace_items(brief_id, items)
        print(f"{path} -> brief_id={brief_id}, items={len(items)}")


if __name__ == "__main__":
    main()
