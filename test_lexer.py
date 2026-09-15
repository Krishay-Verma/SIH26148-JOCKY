from jocky.language.lexer import tokenize
from jocky.language.parser import parse

script = '''
investigation "Endpoint Triage" {
    collect system_info;
    collect processes;
    analyze suspicious_processes;
    report "triage_report";
}
'''

tokens = tokenize(script)
investigation = parse(tokens)
print(investigation)