from datetime import datetime, timezone

from jocky.language.lexer import tokenize
from jocky.language.parser import parse
from jocky.language.interpreter import run_investigation
from jocky.reports.builder import build_report
from jocky.reports.json_writer import write_json_report
from jocky.reports.html_writer import write_html_report

script = '''
investigation "Endpoint Triage" {
    collect system_info;
    collect processes;
    collect network_connections;
    analyze suspicious_processes;
    analyze missing_paths;
    analyze process_network_correlation;
    report "triage_report";
}
'''

started_at = datetime.now(timezone.utc)
investigation = parse(tokenize(script))
result = run_investigation(investigation)
finished_at = datetime.now(timezone.utc)

report = build_report(result, started_at, finished_at)

write_json_report(report, "triage_report.json")
write_html_report(report, "triage_report.html")

print(f"Findings: {len(report.findings)}")
print("Wrote triage_report.json and triage_report.html")