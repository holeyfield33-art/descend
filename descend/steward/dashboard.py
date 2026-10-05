"""Loopback-only, read-only review dashboard. Never renders model HTML."""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from descend.steward.watch import ReviewStore


def render_reviews(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        review = row.get("review") or {}
        findings = review.get("findings") or []
        heading = f"{escape(str(row.get('repo', 'unknown')))} · {escape(str(row.get('sha', ''))[:12])}"
        findings_html = "".join(
            "<li><strong>" + escape(str(item.get("severity", ""))) + "</strong> "
            + escape(str(item.get("path", ""))) + ":" + escape(str(item.get("line", "")))
            + "<p>" + escape(str(item.get("reason", ""))) + "</p>"
            + "<pre>" + escape(str(item.get("evidence", ""))) + "</pre>"
            + ("<p>Line corrected from model citation " + escape(str(item.get("reported_line")))
               + " by exact added-line match.</p>" if item.get("line_corrected") else "")
            + "<p>Check: " + escape(str(item.get("verification", ""))) + "</p></li>"
            for item in findings)
        note = review.get("parse_error") or ("No cited findings" if not findings else "")
        if review.get("rejected"):
            note += f" · {len(review['rejected'])} unsupported citation(s) withheld"
        cards.append(f"<article><h2>{heading}</h2><p>Status: {escape(str(row.get('status', '')))} · "
                     f"Findings: {len(findings)} · Upper-bound cost: "
                     f"${float(review.get('accounted_upper_bound_usd') or 0):.6f}</p>"
                     f"<p>{escape(note)}</p><ul>{findings_html}</ul></article>")
    content = "".join(cards) or "<p>No reviews yet. Start the watcher in another terminal.</p>"
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' "
            "content='width=device-width,initial-scale=1'><title>Repo Steward</title>"
            "<style>body{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;"
            "background:#101820;color:#eef}article{background:#1c2935;padding:1rem 1.4rem;"
            "margin:1rem 0;border-radius:12px}pre{white-space:pre-wrap;background:#10202b;padding:.7rem}"
            "li{margin:1rem 0}small{color:#abc}</style><h1>Repo Steward</h1>"
            "<small>Local, read-only review queue. Citations match added diff lines; bug claims still need verification.</small>"
            + content + "</html>")


def serve_dashboard(store: ReviewStore, port: int = 8765) -> None:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Invalid port")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/":
                self.send_error(404)
                return
            body = render_reviews(store.recent()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        print(f"Repo Steward dashboard: http://127.0.0.1:{port}/", flush=True)
        server.serve_forever()
    finally:
        server.server_close()
