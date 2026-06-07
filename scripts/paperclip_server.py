import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.db import (
    get_items_for_brief,
    get_latest_brief,
    list_recent_feedback,
    list_recent_runs,
    save_feedback,
    reveal_next_item,
)
from paper_company.prompts import get_agent_for_weekday


HOST = "127.0.0.1"
PORT = 8720
FEEDBACK_PATH = ROOT / "paper_company" / "recent_feedback.json"


def row_to_dict(row) -> dict:
    result = {}
    for key in row.keys():
        val = row[key]
        result[key] = str(val) if val is not None else None
    return result


def latest_payload() -> dict:
    weekday = datetime.now().weekday()
    today_agent = get_agent_for_weekday(weekday)["name"]

    brief = get_latest_brief()
    if brief is None:
        return {
            "brief": None,
            "items": [],
            "feedback": [row_to_dict(row) for row in list_recent_feedback()],
            "runs": [row_to_dict(row) for row in list_recent_runs()],
            "today_agent": today_agent,
        }

    brief_data = row_to_dict(brief)
    items = [row_to_dict(row) for row in get_items_for_brief(int(brief["id"]))]
    feedback = [row_to_dict(row) for row in list_recent_feedback()]
    runs = [row_to_dict(row) for row in list_recent_runs()]
    return {
        "brief": brief_data,
        "items": items,
        "feedback": feedback,
        "runs": runs,
        "today_agent": today_agent,
    }


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


class PaperclipHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(INDEX_HTML)
            return
        if parsed.path == "/api/latest":
            self.send_json(latest_payload())
            return
        if parsed.path == "/health":
            self.send_json({"ok": True})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/next":
            brief = get_latest_brief()
            if brief is None:
                self.send_json({"ok": False, "error": "no brief"}, status=404)
                return

            item = reveal_next_item(int(brief["id"]))
            if item is None:
                self.send_json({"ok": False, "exhausted": True})
                return

            self.send_json({"ok": True, "item": row_to_dict(item)})
            return

        if parsed.path != "/api/feedback":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw or "{}")

        feedback_type = str(payload.get("feedback_type") or "").strip()
        note = str(payload.get("note") or "").strip()
        brief_id = payload.get("brief_id")
        item_id = payload.get("item_id")

        if feedback_type not in {"save", "like", "dislike", "acted_on", "make_content"}:
            self.send_json({"ok": False, "error": "unsupported feedback_type"}, status=400)
            return

        feedback_id = save_feedback(
            feedback_type=feedback_type,
            note=note,
            brief_id=int(brief_id) if brief_id else None,
            item_id=int(item_id) if item_id else None,
        )
        refresh_recent_feedback_file()
        self.send_json({"ok": True, "feedback_id": feedback_id})

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(f"[paperclip] {self.address_string()} - {format % args}")


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Paperclip</title>
  <style>
    :root {
      --bg: #f6f3ee;
      --ink: #24211d;
      --muted: #6f6860;
      --line: #d8d1c7;
      --panel: #fffdf8;
      --green: #20745a;
      --yellow: #c2861f;
      --red: #b7443e;
      --blue: #2f5f91;
      --shadow: 0 12px 30px rgba(64, 51, 35, .08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }

    button, input, textarea { font: inherit; }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
    }

    .sidebar {
      border-right: 1px solid var(--line);
      padding: 22px 18px;
      background: #eee8dd;
      position: sticky;
      top: 0;
      height: 100vh;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 26px;
    }

    .clip {
      width: 26px;
      height: 34px;
      border: 3px solid var(--ink);
      border-radius: 13px;
      position: relative;
      transform: rotate(10deg);
    }

    .clip:after {
      content: "";
      position: absolute;
      inset: 6px 5px;
      border: 2px solid var(--ink);
      border-radius: 9px;
      border-bottom-color: transparent;
    }

    h1 {
      font-size: 21px;
      line-height: 1;
      margin: 0;
      letter-spacing: 0;
    }

    .subtitle {
      color: var(--muted);
      font-size: 13px;
      margin-top: 5px;
    }

    .agent-list {
      display: grid;
      gap: 8px;
      margin: 18px 0 28px;
    }

    .agent {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.45);
      border-radius: 8px;
      font-size: 14px;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 0 3px rgba(32,116,90,.12);
    }

    .dot.warn {
      background: var(--yellow);
      box-shadow: 0 0 0 3px rgba(194,134,31,.14);
    }

    .side-section {
      margin-top: 26px;
    }

    .side-title {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 9px;
    }

    .history {
      display: grid;
      gap: 9px;
      font-size: 13px;
      color: var(--muted);
    }

    .content {
      padding: 24px clamp(18px, 4vw, 46px) 40px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 22px;
    }

    .date {
      color: var(--muted);
      margin-top: 7px;
      font-size: 14px;
    }

    .refresh {
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 8px;
      padding: 9px 12px;
      cursor: pointer;
      box-shadow: var(--shadow);
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 20px;
      align-items: start;
    }

    .status-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }

    .status-cell {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 12px;
      min-height: 72px;
      box-shadow: var(--shadow);
    }

    .status-label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }

    .status-value {
      font-size: 15px;
      line-height: 1.35;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #f7f2e9;
    }

    .status-success {
      color: var(--green);
      background: #e6f0ea;
      border-color: #bdd6ca;
    }

    .status-error, .status-timeout {
      color: var(--red);
      background: #f7e8e5;
      border-color: #e2bcb7;
    }

    .status-running {
      color: var(--yellow);
      background: #f8efd9;
      border-color: #e8d199;
    }

    .cards {
      display: grid;
      gap: 14px;
    }

    .card, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .card {
      padding: 18px;
    }

    .card-head {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    .category {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 4px 9px;
      background: #e6f0ea;
      color: var(--green);
      font-size: 12px;
      white-space: nowrap;
    }

    .score {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    h2 {
      margin: 0;
      font-size: 22px;
      line-height: 1.24;
      letter-spacing: 0;
    }

    .hook {
      color: var(--muted);
      margin: 8px 0 14px;
      line-height: 1.55;
    }

    .field {
      border-top: 1px solid var(--line);
      padding-top: 10px;
      margin-top: 10px;
      display: grid;
      gap: 3px;
    }

    .label {
      color: var(--muted);
      font-size: 12px;
    }

    .value {
      line-height: 1.55;
      white-space: pre-wrap;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 15px;
    }

    .actions button {
      border: 1px solid var(--line);
      background: #f7f2e9;
      color: var(--ink);
      border-radius: 8px;
      min-height: 34px;
      padding: 7px 10px;
      cursor: pointer;
    }

    .actions button:hover, .refresh:hover {
      border-color: #bcb1a4;
    }

    .actions button.active {
      background: var(--ink);
      border-color: var(--ink);
      color: #fffdf8;
    }

    .feedback-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }

    .feedback-chip {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 8px;
      background: #efe7d9;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
    }

    .feedback-chip.strong {
      background: #e6f0ea;
      color: var(--green);
      border-color: #bdd6ca;
    }

    .panel {
      padding: 16px;
      position: sticky;
      top: 24px;
    }

    .panel h3 {
      margin: 0 0 12px;
      font-size: 16px;
    }

    textarea {
      width: 100%;
      min-height: 104px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fffaf0;
      padding: 10px;
      color: var(--ink);
    }

    .feedback-row {
      display: flex;
      gap: 8px;
      margin-top: 9px;
    }

    .feedback-row button {
      flex: 1;
      border: 1px solid var(--line);
      background: var(--ink);
      color: #fffdf8;
      border-radius: 8px;
      padding: 9px;
      cursor: pointer;
    }

    .log {
      display: grid;
      gap: 8px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
      max-height: 320px;
      overflow: auto;
    }

    .below-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 20px;
      margin-top: 20px;
    }

    .wide-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 16px;
    }

    .wide-panel h3 {
      margin: 0 0 12px;
      font-size: 16px;
    }

    .record-list {
      display: grid;
      gap: 10px;
      max-height: 520px;
      overflow: auto;
    }

    .record {
      border-top: 1px solid var(--line);
      padding-top: 10px;
      display: grid;
      gap: 5px;
    }

    .record:first-child {
      border-top: 0;
      padding-top: 0;
    }

    .record-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      font-size: 13px;
    }

    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--muted);
    }

    .empty {
      padding: 18px;
      color: var(--muted);
    }

    a {
      color: var(--blue);
      text-decoration: none;
    }

    a:hover { text-decoration: underline; }

    .next-btn {
      width: 100%;
      padding: 14px;
      margin-top: 10px;
      border: 2px dashed var(--line);
      background: transparent;
      color: var(--muted);
      border-radius: 8px;
      cursor: pointer;
      font-size: 15px;
      font-weight: 500;
      transition: all 0.15s ease;
    }

    .next-btn:hover:not(:disabled) {
      border-color: var(--ink);
      color: var(--ink);
      background: var(--panel);
    }

    .next-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    @media (max-width: 920px) {
      .app {
        grid-template-columns: 1fr;
      }
      .sidebar {
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .grid {
        grid-template-columns: 1fr;
      }
      .status-strip, .below-grid {
        grid-template-columns: 1fr;
      }
      .panel {
        position: static;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="clip" aria-hidden="true"></div>
        <div>
          <h1>Paperclip</h1>
          <div class="subtitle">Paper Company control room</div>
        </div>
      </div>
      <div class="side-title">Agents</div>
      <div class="agent-list">
        <div class="agent"><span>AI Agent</span><span class="dot"></span></div>
        <div class="agent"><span>Backend Agent</span><span class="dot"></span></div>
        <div class="agent"><span>Money Agent</span><span class="dot warn"></span></div>
        <div class="agent"><span>People Agent</span><span class="dot"></span></div>
        <div class="agent"><span>Inspiration Rank</span><span class="dot"></span></div>
      </div>
      <div class="side-section">
        <div class="side-title">Latest Feedback</div>
        <div id="sideFeedback" class="history"></div>
      </div>
    </aside>

    <main class="content">
      <div class="topbar">
        <div>
          <h1>Morning Signal</h1>
          <div id="briefDate" class="date">Loading...</div>
        </div>
        <button class="refresh" onclick="loadData()">Refresh</button>
      </div>

      <section class="status-strip" aria-label="Run status">
        <div class="status-cell">
          <div class="status-label">n8n Run</div>
          <div id="latestRunStatus" class="status-value">-</div>
        </div>
        <div class="status-cell">
          <div class="status-label">Trigger</div>
          <div id="latestRunTrigger" class="status-value">-</div>
        </div>
        <div class="status-cell">
          <div class="status-label">Duration</div>
          <div id="latestRunDuration" class="status-value">-</div>
        </div>
        <div class="status-cell">
          <div class="status-label">Last Started</div>
          <div id="latestRunStarted" class="status-value">-</div>
        </div>
      </section>

      <div class="grid">
        <section id="cards" class="cards"></section>
        <aside class="panel">
          <h3>Quick Feedback</h3>
          <textarea id="note" placeholder="오늘 결과에 대한 피드백을 남겨줘. 예: 주식/ERP 비중은 좋고, AI 릴리즈는 줄여줘."></textarea>
          <div class="feedback-row">
            <button onclick="sendGlobalFeedback('feedback')">Feedback</button>
            <button onclick="sendGlobalFeedback('save')">Save</button>
          </div>
          <div class="side-section">
            <div class="side-title">Run State</div>
            <div id="runState" class="history"></div>
          </div>
        </aside>
      </div>

      <section class="below-grid">
        <div class="wide-panel">
          <h3>Execution Logs</h3>
          <div id="runLogs" class="record-list"></div>
        </div>
        <div class="wide-panel">
          <h3>Feedback History</h3>
          <div id="feedbackHistory" class="record-list"></div>
        </div>
      </section>
    </main>
  </div>

  <script>
    let state = { brief: null, items: [], feedback: [], runs: [] };

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function field(label, value) {
      if (!value) return "";
      return `<div class="field"><div class="label">${label}</div><div class="value">${escapeHtml(value)}</div></div>`;
    }

    function fieldHtml(label, value) {
      if (!value) return "";
      return `<div class="field"><div class="label">${label}</div><div class="value">${value}</div></div>`;
    }

    function itemCard(item, index) {
      const source = item.url
        ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.source || "Source")}</a>`
        : escapeHtml(item.source || "");
      const itemFeedback = feedbackForItem(item.id);
      return `
        <article class="card">
          <div class="card-head">
            <div>
              <span class="category">${escapeHtml(item.category || "Signal")}</span>
              <h2>${index + 1}. ${escapeHtml(item.title)}</h2>
            </div>
            <div class="score">${item.score ? `${item.score}/10` : ""}</div>
          </div>
          ${item.hook ? `<div class="hook">${escapeHtml(item.hook)}</div>` : ""}
          ${fieldHtml("Source", source)}
          ${field("Why Now", item.why_now)}
          ${field("Why Fit", item.why_fit)}
          ${field("Next Action", item.next_action)}
          ${field("Expansion", item.expansion)}
          ${field("Exploration Path", item.exploration_path)}
          ${feedbackChips(itemFeedback)}
          <div class="actions">
            ${feedbackButton(item, itemFeedback, "save", "Save")}
            ${feedbackButton(item, itemFeedback, "like", "Like")}
            ${feedbackButton(item, itemFeedback, "dislike", "Dislike")}
            ${feedbackButton(item, itemFeedback, "acted_on", "Acted")}
            ${feedbackButton(item, itemFeedback, "make_content", "Content")}
          </div>
        </article>
      `;
    }

    function feedbackForItem(itemId) {
      return (state.feedback || []).filter((row) => row.item_id === itemId);
    }

    function feedbackCounts(feedbackRows) {
      return feedbackRows.reduce((counts, row) => {
        counts[row.feedback_type] = (counts[row.feedback_type] || 0) + 1;
        return counts;
      }, {});
    }

    function feedbackButton(item, feedbackRows, type, label) {
      const counts = feedbackCounts(feedbackRows);
      const active = counts[type] ? " active" : "";
      const buttonLabel = counts[type] ? `${label} ${counts[type]}` : label;
      return `<button class="${active}" onclick="sendItemFeedback(${item.id}, '${type}')">${buttonLabel}</button>`;
    }

    function feedbackChips(feedbackRows) {
      const counts = feedbackCounts(feedbackRows);
      const entries = Object.entries(counts);
      if (!entries.length) {
        return `<div class="feedback-chips"><span class="feedback-chip">No feedback yet</span></div>`;
      }
      return `
        <div class="feedback-chips">
          ${entries.map(([type, count]) => `<span class="feedback-chip strong">${escapeHtml(type)} ${count}</span>`).join("")}
        </div>
      `;
    }

    function statusClass(status) {
      return `status-${String(status || "").toLowerCase()}`;
    }

    function formatDuration(ms) {
      if (!ms && ms !== 0) return "-";
      if (ms < 1000) return `${ms}ms`;
      const seconds = Math.round(ms / 1000);
      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const rest = seconds % 60;
      return `${minutes}m ${rest}s`;
    }

    function compactLog(text) {
      if (!text) return "";
      const lines = String(text).trim().split("\n").filter(Boolean);
      return lines.slice(-8).join("\n");
    }

    function runRecord(run) {
      const output = compactLog(run.stderr || run.error || run.stdout || "");
      return `
        <div class="record">
          <div class="record-head">
            <span><span class="status-pill ${statusClass(run.status)}">${escapeHtml(run.status)}</span> ${escapeHtml(run.service)}</span>
            <span>${escapeHtml(run.started_at || "")}</span>
          </div>
          <div class="date">${escapeHtml(run.trigger_type)} · ${formatDuration(run.duration_ms)} · rc ${run.returncode ?? "-"}</div>
          ${output ? `<div class="mono">${escapeHtml(output)}</div>` : `<div class="mono">no log output</div>`}
        </div>
      `;
    }

    function feedbackRecord(row) {
      const target = row.item_title ? row.item_title : "Morning Signal";
      return `
        <div class="record">
          <div class="record-head">
            <span><span class="status-pill">${escapeHtml(row.feedback_type)}</span></span>
            <span>${escapeHtml(row.created_at || "")}</span>
          </div>
          <div>${escapeHtml(row.note || row.item_title || "")}</div>
          <div class="date">${escapeHtml(row.brief_date || "-")} · ${escapeHtml(target)}</div>
        </div>
      `;
    }

    async function loadData() {
      const response = await fetch("/api/latest");
      state = await response.json();
      render();
    }

    function render() {
      const briefDate = document.getElementById("briefDate");
      const cards = document.getElementById("cards");
      const runState = document.getElementById("runState");
      const sideFeedback = document.getElementById("sideFeedback");
      const latestRun = state.runs && state.runs.length ? state.runs[0] : null;
      const runLogs = document.getElementById("runLogs");
      const feedbackHistory = document.getElementById("feedbackHistory");

      if (!state.brief) {
        briefDate.textContent = "No brief yet";
        cards.innerHTML = `<div class="card empty">아직 저장된 Morning Signal이 없습니다.</div>`;
        runState.innerHTML = "";
        sideFeedback.innerHTML = "";
        renderRunSummary(latestRun);
        renderHistory(runLogs, feedbackHistory);
        return;
      }

      briefDate.textContent = `${state.brief.run_date} · updated ${state.brief.updated_at}`;

      const hasDeepDive = state.items.some((i) => i.status === "active");
      let cardsHtml = "";

      if (hasDeepDive) {
        const activeItem = state.items.find((i) => i.status === "active");
        const revealedItems = state.items.filter((i) => i.status === "revealed");
        const visibleItems = [activeItem, ...revealedItems].filter(Boolean);
        cardsHtml = visibleItems.length ? visibleItems.map(itemCard).join("") : `<div class="card empty">아이템을 찾을 수 없습니다.</div>`;

        const hasCandidate = state.items.some((i) => i.status === "candidate");
        if (hasCandidate) {
          cardsHtml += `<button id="nextBtn" class="next-btn" onclick="handleNext()">Next →</button>`;
        }
      } else {
        cardsHtml = state.items.length
          ? state.items.map(itemCard).join("")
          : `<div class="card empty">아이템 파싱 결과가 없습니다. 원문은 SQLite briefs에 저장되어 있습니다.</div>`;
      }

      cards.innerHTML = cardsHtml;

      runState.innerHTML = [
        `Brief ID: ${state.brief.id}`,
        `Items: ${state.items.length}`,
        `Markdown: ${state.brief.markdown_path || "-"}`,
        `Latest Run: ${latestRun ? latestRun.status : "-"}`
      ].map((line) => `<div>${escapeHtml(line)}</div>`).join("");

      sideFeedback.innerHTML = state.feedback.length
        ? state.feedback.slice(0, 8).map((row) => `<div>${escapeHtml(row.feedback_type)} · ${escapeHtml(row.note || row.item_title || "")}</div>`).join("")
        : `<div>아직 피드백 없음</div>`;

      renderRunSummary(latestRun);
      renderHistory(runLogs, feedbackHistory);
    }

    function renderRunSummary(latestRun) {
      document.getElementById("latestRunStatus").innerHTML = latestRun
        ? `<span class="status-pill ${statusClass(latestRun.status)}">${escapeHtml(latestRun.status)}</span>`
        : "-";
      document.getElementById("latestRunTrigger").textContent = latestRun ? latestRun.trigger_type : "-";
      document.getElementById("latestRunDuration").textContent = latestRun ? formatDuration(latestRun.duration_ms) : "-";
      document.getElementById("latestRunStarted").textContent = latestRun ? latestRun.started_at : "-";
    }

    function renderHistory(runLogs, feedbackHistory) {
      runLogs.innerHTML = state.runs && state.runs.length
        ? state.runs.map(runRecord).join("")
        : `<div class="empty">아직 실행 로그가 없습니다. n8n에서 실행하면 여기에 남습니다.</div>`;
      feedbackHistory.innerHTML = state.feedback && state.feedback.length
        ? state.feedback.map(feedbackRecord).join("")
        : `<div class="empty">아직 피드백 히스토리가 없습니다.</div>`;
    }

    async function postFeedback(payload) {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const error = await response.json();
        alert(error.error || "feedback failed");
        return;
      }
      await loadData();
    }

    function sendItemFeedback(itemId, feedbackType) {
      const item = state.items.find((candidate) => candidate.id === itemId);
      postFeedback({
        feedback_type: feedbackType,
        brief_id: state.brief && state.brief.id,
        item_id: itemId,
        note: item ? item.title : ""
      });
    }

    function sendGlobalFeedback(feedbackType) {
      const note = document.getElementById("note").value.trim();
      if (!note) return;
      document.getElementById("note").value = "";
      postFeedback({
        feedback_type: feedbackType,
        brief_id: state.brief && state.brief.id,
        note
      });
    }

    async function handleNext() {
      const btn = document.getElementById("nextBtn");
      if (btn) btn.disabled = true;

      const response = await fetch("/api/next", { method: "POST" });
      const data = await response.json();

      if (data.exhausted) {
        alert("오늘의 후보를 모두 확인했습니다.");
        await loadData();
        return;
      }

      if (!data.ok) {
        alert("Next 로드 실패");
        if (btn) btn.disabled = false;
        return;
      }

      const idx = state.items.findIndex((i) => i.id === data.item.id);
      if (idx !== -1) {
        state.items[idx] = data.item;
      }
      render();
    }

    loadData();
  </script>
</body>
</html>
"""


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PaperclipHandler)
    print(f"Paperclip UI running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
