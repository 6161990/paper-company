import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_company.db import finish_run, start_run

PYTHON = ROOT / ".venv" / "bin" / "python"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "paper-company-runner"})
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/run/explore":
            self._json(404, {"ok": False, "error": "not_found"})
            return

        run_id = start_run(service="morning_signal", trigger_type="n8n_local_runner")
        try:
            proc = subprocess.run(
                [str(PYTHON), "scripts/explore_daily.py"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=900,
            )
        except subprocess.TimeoutExpired as exc:
            finish_run(
                run_id,
                status="timeout",
                stdout=exc.stdout,
                stderr=exc.stderr,
                error="explore_daily.py timed out after 900 seconds",
            )
            self._json(
                504,
                {
                    "ok": False,
                    "run_id": run_id,
                    "error": "timeout",
                    "stdout": exc.stdout,
                    "stderr": exc.stderr,
                },
            )
            return

        finish_run(
            run_id,
            status="success" if proc.returncode == 0 else "error",
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
        self._json(
            200 if proc.returncode == 0 else 500,
            {
                "ok": proc.returncode == 0,
                "run_id": run_id,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        print(f"[runner] {self.address_string()} - {format % args}")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = HTTPServer(("0.0.0.0", 8711), Handler)
    print("Paper Company local runner listening on http://127.0.0.1:8711")
    server.serve_forever()


if __name__ == "__main__":
    main()
