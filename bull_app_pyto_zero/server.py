import html
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from screener import default_start_date, run_screener
from storage import RESULTS_FILE, SKIPPED_FILE, last_run_time, read_csv


class ScreenerHandler(BaseHTTPRequestHandler):
    def _send_html(self, body, status=200):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path, content_type="text/csv"):
        if not os.path.exists(path):
            self._send_html("<h1>Not found</h1>", 404)
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        if content_type == "text/csv":
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send_html(home_page())
        elif self.path == "/results":
            self._send_html(results_page())
        elif self.path == "/download/results.csv":
            self._send_file(RESULTS_FILE, "text/csv")
        elif self.path == "/download/skipped.csv":
            self._send_file(SKIPPED_FILE, "text/csv")
        elif self.path == "/static/style.css":
            css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "style.css")
            self._send_file(css_path, "text/css")
        else:
            self._send_html("<h1>404</h1>", 404)

    def do_POST(self):
        if self.path != "/run":
            self._send_html("<h1>404</h1>", 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(body)
        start_date = form.get("start_date", [default_start_date()])[0]
        top_n = int(form.get("top_n", ["25"])[0] or "25")
        strict_mode = form.get("strict_mode", ["off"])[0] == "on"
        include_macro = form.get("include_macro", ["off"])[0] == "on"
        run_screener(start_date=start_date, top_n=top_n, strict_mode=strict_mode, include_macro=include_macro)
        self.send_response(303)
        self.send_header("Location", "/results")
        self.end_headers()


def layout(title, content):
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{html.escape(title)}</title><link rel='stylesheet' href='/static/style.css'></head>
<body><main class='container'>{content}</main></body></html>"""


def home_page():
    content = f"""
<h1>bull_app_pyto_zero</h1>
<p>Universe: NASDAQ-100 (bundled list)</p>
<p>Last run time: {html.escape(last_run_time())}</p>
<form method='post' action='/run'>
<label>Start date <input type='date' name='start_date' value='{default_start_date()}'></label>
<label>Top N <input type='number' name='top_n' value='25' min='1' max='100'></label>
<label><input type='checkbox' name='strict_mode'> Strict mode</label>
<label><input type='checkbox' name='include_macro'> Include macro gates</label>
<button type='submit'>Run Screener</button>
</form>
<p><a class='btn secondary' href='/results'>View latest results</a></p>
"""
    return layout("Home", content)


def results_page():
    rows = read_csv(RESULTS_FILE)
    skipped = read_csv(SKIPPED_FILE)
    headers = [
        "ticker", "score", "price", "sma50", "sma200", "golden_cross_recent", "price_above_200", "sma200_up",
        "rsi14", "rsi_regime", "macd", "macd_signal", "macd_hist", "macd_bullish", "atr_pct", "atr_contraction_breakout", "rs_up", "reasons",
    ]
    head_html = "".join(f"<th>{h}</th>" for h in headers)
    body_html = "".join("<tr>" + "".join(f"<td>{html.escape(r.get(h, ''))}</td>" for h in headers) + "</tr>" for r in rows)
    skipped_html = "".join(f"<li>{html.escape(s.get('ticker',''))}: {html.escape(s.get('reason',''))}</li>" for s in skipped)
    content = f"""
<h1>Results</h1>
<p>Last run time: {html.escape(last_run_time())} | passed: {len(rows)} | skipped: {len(skipped)}</p>
<p><a class='btn' href='/'>Home</a> <a class='btn' href='/download/results.csv'>Download CSV</a> <a class='btn secondary' href='/download/skipped.csv'>Download Skipped CSV</a></p>
<div class='table-wrap'><table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table></div>
<h2>Skipped tickers</h2>
<ul>{skipped_html or '<li>None</li>'}</ul>
"""
    return layout("Results", content)


def run_server(port=8000):
    server = HTTPServer(("127.0.0.1", port), ScreenerHandler)
    print(f"Serving on http://127.0.0.1:{port}")
    server.serve_forever()
