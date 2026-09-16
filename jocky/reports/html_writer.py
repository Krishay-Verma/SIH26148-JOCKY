"""
Writes a Report as a readable HTML document.

Uses plain Python string building (no templating library) since the
report layout is simple and static. Keeping this dependency-free means
one less library to explain and one less thing that can break.

Provides two functions:
  - build_html_string(report) -> str   (used by the API to serve downloads)
  - write_html_report(report, path)    (used by CLI scripts to write a file)
"""

from html import escape
from pathlib import Path

from jocky.reports.report import Report


def build_html_string(report: Report) -> str:
    """Return the full HTML report as a string."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JOCKY Report - {escape(report.investigation_name)}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 40px; color: #1a1a1a; max-width: 960px; }}
  h1 {{ font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-bottom: 4px; }}
  h2 {{ font-size: 15px; margin-top: 32px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 8px; font-size: 13px; }}
  th, td {{ text-align: left; padding: 7px 12px; border-bottom: 1px solid #eee; }}
  th {{ color: #666; font-weight: 600; background: #f7f7f8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .meta {{ color: #555; font-size: 13px; margin: 3px 0; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }}
  .sev-informational     {{ background: #f0f0f0; color: #555; }}
  .sev-review_recommended {{ background: #fef3e2; color: #a15c00; }}
  .status-success {{ background: #e8f5ee; color: #18794e; }}
  .status-error   {{ background: #fdecea; color: #b00020; }}
  code {{ font-family: monospace; font-size: 12px; }}
</style>
</head>
<body>
  <h1>JOCKY Investigation Report</h1>
  <p class="meta"><strong>Investigation:</strong> {escape(report.investigation_name)}</p>
  <p class="meta"><strong>Endpoint:</strong> {escape(report.endpoint_hostname)}</p>
  <p class="meta"><strong>Started:</strong> {escape(report.started_at)}</p>
  <p class="meta"><strong>Finished:</strong> {escape(report.finished_at)}</p>

  <h2>Collector Status</h2>
  <table>
    <tr><th>Collector</th><th>Status</th><th>Detail</th></tr>
    {_collector_rows(report)}
  </table>

  <h2>Findings ({len(report.findings)})</h2>
  <table>
    <tr><th>Rule</th><th>Severity</th><th>Summary</th><th>Reason</th></tr>
    {_finding_rows(report)}
  </table>
</body>
</html>"""


def write_html_report(report: Report, output_path: str) -> None:
    """Write the HTML report to a file at output_path."""
    Path(output_path).write_text(build_html_string(report), encoding="utf-8")


def _collector_rows(report: Report) -> str:
    rows = []
    for cr in report.collector_results:
        css = "status-error" if cr.status == "error" else "status-success"
        detail = cr.error if cr.status == "error" else "OK"
        rows.append(
            f"<tr>"
            f"<td><code>{escape(cr.target)}</code></td>"
            f'<td><span class="badge {css}">{escape(cr.status)}</span></td>'
            f"<td>{escape(str(detail))}</td>"
            f"</tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='3'>No collectors ran</td></tr>"


def _finding_rows(report: Report) -> str:
    rows = []
    for f in report.findings:
        rows.append(
            f"<tr>"
            f"<td><code>{escape(f.rule_name)}</code></td>"
            f'<td><span class="badge sev-{escape(f.severity)}">{escape(f.severity)}</span></td>'
            f"<td>{escape(f.summary)}</td>"
            f"<td>{escape(f.reason)}</td>"
            f"</tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='4'>No findings</td></tr>"