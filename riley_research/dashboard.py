"""Read-only local dashboard for sanitized evidence records."""
import html
import json
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .evidence import EvidenceStore
from .track_c_analysis import comparison_rows


def render(records, selected_track=None, cases=None):
    visible = [r for r in records if not selected_track or r.get("track") == selected_track]
    tracks = Counter(r.get("track") for r in visible)
    outcomes = Counter(r.get("evaluation_result") for r in visible)
    models = Counter((r.get("track"), r.get("model")) for r in visible)
    boundaries = Counter((r.get("boundary"), r.get("evaluation_result")) for r in visible)
    c_records = [r for r in visible if r.get("track") == "C"]
    c_attempts = sum(bool(r.get("requested_tool_calls")) for r in c_records)
    c_executor = sum(r.get("executed_tool_calls") is not None and r.get("observed_tool_results") is not None for r in c_records)
    c_database = sum(r.get("database_observation") is not None for r in c_records)
    cases = cases or []
    categories = Counter(c.get("category") for c in cases)
    tokens = sum(r.get("token_usage") or 0 for r in visible if isinstance(r.get("token_usage"), (int, float)))
    estimated_cost = sum(r.get("estimated_cost") or 0 for r in visible if isinstance(r.get("estimated_cost"), (int, float)))
    def esc(v):
        return html.escape(str(v if v is not None else "—"))
    def table(headers, rows):
        return "<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(
            "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows) + "</tbody></table>"
    total = len(visible)
    sections = [f"<h1>Riley Research Evidence</h1><p>{total} trials. Synthetic tracks and authorized observations are separate.</p>",
        '<nav><a href="/">All</a> <a href="/?track=A">Mock</a> <a href="/?track=B">Local LLM</a> <a href="/?track=C">Riley</a></nav>',
        "<h2>Outcomes</h2>" + table(("Outcome", "Count", "Rate"), ((k, v, f"{v}/{total}") for k, v in sorted(outcomes.items()))),
        "<h2>Tracks</h2>" + table(("Track", "Trials"), sorted(tracks.items())),
        "<h2>Case inventory and taxonomy</h2>" + table(("Category", "Cases"), sorted(categories.items())),
        table(("Case", "Category", "Boundary", "Required tracks"), ((c.get("case_id"), c.get("category"), c.get("target_boundary"), ", ".join(c.get("required_tracks") or [])) for c in cases)),
        "<h2>Models</h2>" + table(("Track", "Model", "Trials"), ((a, b, n) for (a, b), n in sorted(models.items(), key=str))),
        "<h2>Track and configuration comparison</h2>" + table(("Track", "Model", "Configuration", "Trials", "PASS", "FAIL", "INCONCLUSIVE", "ERROR", "NOT_RUN"), comparison_rows(visible)),
        "<h2>Boundaries</h2>" + table(("Boundary", "Outcome", "Trials"), ((a, b, n) for (a, b), n in sorted(boundaries.items(), key=str))),
        f"<h2>Riley observation levels</h2><p>{len(c_records)} Track C trials; {c_attempts} with client-visible tool requests; {c_executor} with independent executor results; {c_database} with independent database observations. A tool request alone does not establish execution.</p>",
        f"<h2>Usage</h2><p>Recorded tokens: {tokens}; estimated cost: {estimated_cost}. Missing usage is excluded.</p>",
        f"<h2>Unresolved hypotheses</h2><p>{outcomes.get('INCONCLUSIVE', 0)} inconclusive trials require further evidence.</p>",
        "<h2>Trials and provenance</h2>" + table(("Time", "Run", "Case", "Track", "Model", "Outcome", "Evidence", "Source", "Reason", "Tokens", "Estimated cost"),
            ((r.get("timestamp"), r.get("run_id"), r.get("case_id"), r.get("track"), r.get("model"), r.get("evaluation_result"), r.get("evidence_status"), r.get("evidence_source"), r.get("evaluation_reason"), r.get("token_usage"), r.get("estimated_cost")) for r in sorted(visible, key=lambda r: str(r.get("timestamp")), reverse=True))),
        "<h2>Trial details</h2>" + "".join(f"<details><summary>{esc(r.get('case_id'))} · {esc(r.get('track'))} · {esc(r.get('evaluation_result'))}</summary><pre>{esc(json.dumps(r, ensure_ascii=False, indent=2))}</pre></details>" for r in visible)]
    return '<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Riley Evidence</title><style>body{font:16px system-ui;max-width:1100px;margin:auto;padding:1rem}table{border-collapse:collapse;display:block;overflow-x:auto;width:100%}td,th{border:1px solid #bbb;padding:.5rem;text-align:left}tr:nth-child(even){background:#eee}nav a{margin-right:1rem}</style>' + "".join(sections) + "</html>"


def serve(path, host="127.0.0.1", port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path != "/":
                self.send_error(404)
                return
            selected = parse_qs(parsed.query).get("track", [None])[0]
            research_dir = Path(__file__).resolve().parent.parent / "research"
            cases = []
            for name in ("cases.json", "track_c_cases.json"):
                case_path = research_dir / name
                if case_path.exists():
                    cases.extend(json.loads(case_path.read_text()))
            body = render(EvidenceStore(path).list(), selected, cases).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
