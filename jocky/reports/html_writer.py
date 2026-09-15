"""
Writes a Report as a readable HTML document.

Uses plain Python string building (no templating library) since the
report layout is simple and static. Keeping this dependency-free means
one less library to explain and one less thing that can break.
"""

from html import escape
from pathlib import Path

from jocky.reports.report import Report


def write_html_report(report: Report, output_path: str) -> None:
    """Write report as a readable HTML file at output_path."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JOCKY Report - {escape(report.investigation_name)}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 40px; color: #1a1a1a; }}
  h1 {{ font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px; }}
  h2 {{ font-size: 16px; margin-top: 32px; color: #333; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #eee; font-size: 13px; }}
  th {{ color: #666; font-weight: 600; }}
  .meta {{ color: #555; font-size: 13px; margin-bottom: 4px; }}
  .sev-informational {{ color: #666; }}
  .sev-review_recommended {{ color: #a15c00; font-weight: 600; }}
  .status-error {{ color: #b00020; }}
</style>
</head>
<body>
  <h1>JOCKY Investigation Report: {escape(report.investigation_name)}</h1>
  <div class="meta">Endpoint: {escape(report.endpoint_hostname)}</div>
  <div class="meta">Started: {escape(report.started_at)}</div>
  <div class="meta">Finished: {escape(report.finished_at)}</div>

  <h2>Collector Status</h2>
  <table>
    <tr><th>Collector</th><th>Status</th><th>Details</th></tr>
    {_render_collector_rows(report)}
  </table>

  <h2>Findings ({len(report.findings)})</h2>
  <table>
    <tr><th>Rule</th><th>Severity</th><th>Summary</th><th>Reason</th></tr>
    {_render_finding_rows(report)}
  </table>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")


def _render_collector_rows(report: Report) -> str:
    rows = []
    for cr in report.collector_results:
        css = "status-error" if cr.status == "error" else ""
        detail = cr.error if cr.status == "error" else "OK"
        rows.append(
            f"<tr><td>{escape(cr.target)}</td>"
            f'<td class="{css}">{escape(cr.status)}</td>'
            f"<td>{escape(str(detail))}</td></tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='3'>No collectors ran</td></tr>"


def _render_finding_rows(report: Report) -> str:
    rows = []
    for f in report.findings:
        rows.append(
            f"<tr><td>{escape(f.rule_name)}</td>"
            f'<td class="sev-{escape(f.severity)}">{escape(f.severity)}</td>'
            f"<td>{escape(f.summary)}</td>"
            f"<td>{escape(f.reason)}</td></tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='4'>No findings</td></tr>"