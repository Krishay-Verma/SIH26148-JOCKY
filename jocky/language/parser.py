"""
Parser for the JOCKY DSL.

Turns a token list (from lexer.py) into an Investigation IR object
(from ir.py). This is a hand-written "recursive descent" parser: we look
at the current token, decide what grammar rule applies, consume tokens
accordingly, and raise ParseError the moment something doesn't match.

The parser does NOT know what "system_info" or "processes" mean, and it
does NOT check whether a collector/rule name is real. That validation
happens later, in the interpreter, against an allowlist registry. The
parser only checks *grammar* (structure), not *semantics* (meaning).
"""

from jocky.language.lexer import Token, TokenType
from jocky.language.ir import (
    Investigation,
    CollectCommand,
    AnalyzeCommand,
    ReportCommand,
    Command,
)

# Keywords allowed to start a statement inside an investigation block.
_STATEMENT_KEYWORDS = {"collect", "analyze", "report"}


class ParseError(Exception):
    """Raised when tokens don't match the expected JOCKY grammar."""
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, type_: TokenType, what: str) -> Token:
        """Consume the current token if it matches type_, else raise ParseError."""
        tok = self._current()
        if tok.type != type_:
            raise ParseError(
                f"Line {tok.line}: expected {what}, got {tok.value!r}"
            )
        return self._advance()

    def _expect_ident(self, value: str) -> Token:
        """Consume the current token if it's the IDENT `value`, else raise ParseError."""
        tok = self._current()
        if tok.type != TokenType.IDENT or tok.value != value:
            raise ParseError(
                f"Line {tok.line}: expected '{value}', got {tok.value!r}"
            )
        return self._advance()

    def parse(self) -> Investigation:
        """Parse a full script: investigation "<name>" { <statements> }"""
        self._expect_ident("investigation")
        name_tok = self._expect(TokenType.STRING, "investigation name (a string)")
        self._expect(TokenType.LBRACE, "'{'")

        commands: list[Command] = []
        while self._current().type != TokenType.RBRACE:
            if self._current().type == TokenType.EOF:
                raise ParseError(
                    f"Line {self._current().line}: reached end of file, missing '}}'"
                )
            commands.append(self._parse_statement())

        self._expect(TokenType.RBRACE, "'}'")
        self._expect(TokenType.EOF, "end of script (unexpected extra content)")

        return Investigation(name=name_tok.value, commands=commands)

    def _parse_statement(self) -> Command:
        """Parse one statement: collect/analyze <ident>; or report "<name>";"""
        tok = self._current()
        if tok.type != TokenType.IDENT or tok.value not in _STATEMENT_KEYWORDS:
            raise ParseError(
                f"Line {tok.line}: expected 'collect', 'analyze', or 'report', "
                f"got {tok.value!r}"
            )
        keyword = self._advance().value

        if keyword in ("collect", "analyze"):
            arg_tok = self._expect(TokenType.IDENT, f"{keyword} target (a name)")
            self._expect(TokenType.SEMICOLON, "';'")
            if keyword == "collect":
                return CollectCommand(target=arg_tok.value, line=arg_tok.line)
            return AnalyzeCommand(rule=arg_tok.value, line=arg_tok.line)

        # keyword == "report"
        arg_tok = self._expect(TokenType.STRING, "report name (a string)")
        self._expect(TokenType.SEMICOLON, "';'")
        return ReportCommand(name=arg_tok.value, line=arg_tok.line)


def parse(tokens: list[Token]) -> Investigation:
    """Convenience wrapper: parse a token list into an Investigation."""
    return Parser(tokens).parse()
