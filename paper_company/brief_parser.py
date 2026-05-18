import re


FIELD_NAMES = {
    "title": "title",
    "hook": "hook",
    "source": "source",
    "why_now": "why_now",
    "why_fit": "why_fit",
    "next_action": "next_action",
    "expansion": "expansion",
    "exploration_path": "exploration_path",
    "category": "category",
}

FIELD_ALIASES = {
    "title": "title",
    "hook": "hook",
    "source": "source",
    "why_now": "why_now",
    "why now": "why_now",
    "why_fit": "why_fit",
    "why fit": "why_fit",
    "next_action": "next_action",
    "next action": "next_action",
    "expansion": "expansion",
    "exploration_path": "exploration_path",
    "exploration path": "exploration_path",
    "category": "category",
}


def parse_brief_items(content: str) -> list[dict]:
    sections = split_item_sections(content)
    return [parse_item_section(section) for section in sections]


def split_item_sections(content: str) -> list[str]:
    pattern = re.compile(r"(?m)^###\s+(?:#?\d+[\).]?\s+)?(.+)$")
    matches = list(pattern.finditer(content))
    sections: list[str] = []

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section = content[start:end].strip()
        heading = match.group(1).strip()
        if heading and not heading.lower().startswith("phase "):
            sections.append(section)

    return sections


def parse_item_section(section: str) -> dict:
    lines = section.splitlines()
    heading = clean_heading(lines[0]) if lines else "Untitled"
    fields = extract_fields(section)

    title = fields.get("title") or heading
    source = fields.get("source")
    url = extract_first_url(source or section)

    item = {
        "title": clean_inline(title),
        "source": clean_inline(source) if source else None,
        "url": url,
        "category": clean_inline(fields.get("category")) if fields.get("category") else infer_category(section),
        "hook": clean_block(fields.get("hook")),
        "why_now": clean_block(fields.get("why_now")),
        "why_fit": clean_block(fields.get("why_fit")),
        "next_action": clean_block(fields.get("next_action")),
        "expansion": clean_block(fields.get("expansion")),
        "exploration_path": clean_block(fields.get("exploration_path")),
        "score": extract_score(section),
    }
    return item


def clean_heading(line: str) -> str:
    value = re.sub(r"^###\s+", "", line).strip()
    value = re.sub(r"^#?\d+[\).]?\s+", "", value).strip()
    return clean_inline(value)


def extract_fields(section: str) -> dict[str, str]:
    field_pattern = re.compile(
        r"(?mi)^\s*(?:\*\*([A-Za-z_ ]+)\*\*|([A-Za-z_ ]+)\s*[:：])\s*(.*)$"
    )
    matches = list(field_pattern.finditer(section))
    fields: dict[str, str] = {}

    for idx, match in enumerate(matches):
        raw_name = (match.group(1) or match.group(2) or "").strip().lower()
        name = FIELD_ALIASES.get(raw_name)
        if name not in FIELD_NAMES:
            continue

        value_start = match.end()
        value_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        inline = match.group(3).strip()
        rest = section[value_start:value_end].strip()
        value = inline
        if rest:
            value = f"{inline}\n{rest}".strip() if inline else rest
        fields[name] = value.strip()

    return fields


def extract_first_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s\)\]]+", text)
    return match.group(0) if match else None


def extract_score(section: str) -> float | None:
    score_match = re.search(r"(?i)\bscore\b[^0-9]*(\d+(?:\.\d+)?)", section)
    if score_match:
        return float(score_match.group(1))

    table_match = re.search(r"\|\s*(\d+(?:\.\d+)?)\s*\|", section)
    if table_match:
        return float(table_match.group(1))

    return None


def infer_category(section: str) -> str | None:
    text = section.lower()
    if any(keyword in text for keyword in ["erp", "회계", "재무", "매출", "영업이익", "현금흐름", "crm", "scm"]):
        return "Business Concept"
    if any(keyword in text for keyword in ["stock", "주식", "증시", "나스닥", "s&p", "earnings"]):
        return "Stock"
    if any(keyword in text for keyword in ["장애", "backend", "infra", "observability", "mysql", "redis", "kafka"]):
        return "Backend"
    if any(keyword in text for keyword in ["claude", "agent", "llm", "ai"]):
        return "AI"
    if any(keyword in text for keyword in ["founder", "창업자", "개발자", "루틴", "작업 방식"]):
        return "Inspiring People"
    return None


def clean_inline(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    value = value.strip("`")
    value = re.sub(r"^\*\*|\*\*$", "", value).strip()
    return value


def clean_block(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    value = re.sub(r"^>\s?", "", value, flags=re.MULTILINE)
    return value
