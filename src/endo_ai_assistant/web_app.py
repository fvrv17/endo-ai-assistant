from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .pipeline import (
    DEMO_INPUT,
    build_extract_response,
)


def run_server(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), EndoAssistantHandler)
    print(f"Serving Endo AI Assistant at http://{host}:{port}")
    server.serve_forever()


class EndoAssistantHandler(BaseHTTPRequestHandler):
    server_version = "EndoAIAssistant/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
        path = urlparse(self.path).path
        if path == "/":
            self._send_text(INDEX_HTML, content_type="text/html; charset=utf-8")
            return
        if path == "/api/health":
            self._send_json({"ok": True})
            return
        if path == "/api/demo":
            self._send_json({"raw_input": DEMO_INPUT})
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API.
        path = urlparse(self.path).path
        if path != "/api/extract":
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            payload = self._read_json()
            self._send_json(build_extract_response(payload))
        except Exception as exc:  # noqa: BLE001 - API should return readable errors.
            self._send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}
        loaded = json.loads(raw_body.decode("utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("JSON body must be an object.")
        return loaded

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(
        self,
        body: str,
        *,
        content_type: str,
        status: int = 200,
    ) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Endo AI Assistant UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)

    run_server(args.host, args.port)
    return 0


INDEX_HTML = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Endo AI Assistant</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --line: #d8dee6;
      --text: #18202a;
      --muted: #657184;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --warn-bg: #fff7ed;
      --warn-line: #fed7aa;
      --code-bg: #101820;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
      font-weight: 700;
    }
    .status {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    main {
      display: grid;
      grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1.1fr);
      min-height: calc(100vh - 55px);
    }
    .pane {
      min-width: 0;
      padding: 18px;
    }
    .pane + .pane {
      border-left: 1px solid var(--line);
      background: #fbfcfd;
    }
    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }
    textarea, input, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      font: inherit;
    }
    textarea {
      min-height: 310px;
      padding: 12px;
      resize: vertical;
      line-height: 1.45;
    }
    input, select {
      height: 38px;
      padding: 0 10px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    button {
      height: 38px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      font-weight: 700;
      cursor: pointer;
    }
    button.primary {
      border-color: var(--accent);
      background: var(--accent);
      color: white;
    }
    button.primary:hover { background: var(--accent-dark); }
    button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .tab {
      height: 34px;
      padding: 0 12px;
      font-size: 13px;
    }
    .tab.active {
      border-color: var(--accent);
      color: var(--accent-dark);
      background: #e6f5f3;
    }
    .output {
      display: none;
      min-height: 420px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      padding: 14px;
      white-space: pre-wrap;
      line-height: 1.5;
      overflow: auto;
    }
    .output.active { display: block; }
    pre.output {
      background: var(--code-bg);
      color: #edf6f9;
      font-size: 13px;
    }
    .error {
      display: none;
      margin: 12px 0;
      padding: 10px 12px;
      border: 1px solid var(--warn-line);
      border-radius: 6px;
      background: var(--warn-bg);
      color: #7c2d12;
      line-height: 1.4;
    }
    .error.visible { display: block; }
    .hint {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }
    @media (max-width: 920px) {
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; }
      .pane + .pane { border-left: 0; border-top: 1px solid var(--line); }
      .grid { grid-template-columns: 1fr; }
      .status { white-space: normal; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Endo AI Assistant</h1>
    <div class="status" id="status">Локальный прототип</div>
  </header>
  <main>
    <section class="pane">
      <label for="rawInput">Свободное описание врача</label>
      <textarea id="rawInput"></textarea>
      <div class="grid">
        <div>
          <label for="examType">Исследование</label>
          <select id="examType">
            <option value="gastroscopy">ЭГДС</option>
            <option value="colonoscopy">Колоноскопия</option>
          </select>
        </div>
        <div>
          <label for="provider">Provider</label>
          <select id="provider">
            <option value="synthetic">Synthetic offline</option>
            <option value="openai">OpenAI structured output</option>
          </select>
        </div>
        <div>
          <label for="indication">Повод</label>
          <input id="indication" placeholder="не указано">
        </div>
        <div>
          <label for="model">OpenAI model</label>
          <input id="model" value="gpt-5.5">
        </div>
      </div>
      <div class="actions">
        <button class="primary" id="extractBtn">Извлечь</button>
        <button id="demoBtn">Демо-текст</button>
        <button id="clearBtn">Очистить</button>
      </div>
      <div class="hint">OpenAI-вызов используется только при выборе provider OpenAI и наличии ключа в окружении сервера.</div>
      <div class="error" id="errorBox"></div>
    </section>
    <section class="pane">
      <div class="tabs">
        <button class="tab active" data-tab="report">Заключение</button>
        <button class="tab" data-tab="stats">Статистика</button>
        <button class="tab" data-tab="json">JSON</button>
      </div>
      <div class="output active" id="reportOutput">Результат появится здесь после извлечения.</div>
      <div class="output" id="statsOutput">Статистика появится здесь после извлечения.</div>
      <pre class="output" id="jsonOutput">{}</pre>
    </section>
  </main>
  <script>
    const rawInput = document.querySelector("#rawInput");
    const examType = document.querySelector("#examType");
    const provider = document.querySelector("#provider");
    const indication = document.querySelector("#indication");
    const model = document.querySelector("#model");
    const extractBtn = document.querySelector("#extractBtn");
    const demoBtn = document.querySelector("#demoBtn");
    const clearBtn = document.querySelector("#clearBtn");
    const errorBox = document.querySelector("#errorBox");
    const status = document.querySelector("#status");
    const outputs = {
      report: document.querySelector("#reportOutput"),
      stats: document.querySelector("#statsOutput"),
      json: document.querySelector("#jsonOutput")
    };

    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
        Object.values(outputs).forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        outputs[tab.dataset.tab].classList.add("active");
      });
    });

    async function loadDemo() {
      const response = await fetch("/api/demo");
      const payload = await response.json();
      rawInput.value = payload.raw_input;
    }

    async function extract() {
      setError("");
      extractBtn.disabled = true;
      status.textContent = "Извлечение...";
      try {
        const response = await fetch("/api/extract", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            raw_input: rawInput.value,
            exam_type: examType.value,
            provider: provider.value,
            indication: indication.value,
            model: model.value
          })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Ошибка извлечения");
        outputs.report.textContent = payload.report_text;
        outputs.stats.textContent = payload.stats_text;
        outputs.json.textContent = JSON.stringify(payload.structured, null, 2);
        status.textContent = `Готово: ${payload.stats.observations_total} находок`;
      } catch (error) {
        setError(error.message);
        status.textContent = "Ошибка";
      } finally {
        extractBtn.disabled = false;
      }
    }

    function setError(message) {
      errorBox.textContent = message;
      errorBox.classList.toggle("visible", Boolean(message));
    }

    demoBtn.addEventListener("click", loadDemo);
    clearBtn.addEventListener("click", () => {
      rawInput.value = "";
      indication.value = "";
      outputs.report.textContent = "Результат появится здесь после извлечения.";
      outputs.stats.textContent = "Статистика появится здесь после извлечения.";
      outputs.json.textContent = "{}";
      status.textContent = "Локальный прототип";
      setError("");
    });
    extractBtn.addEventListener("click", extract);
    loadDemo();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
