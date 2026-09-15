"""
Lexer for the JOCKY DSL.

The lexer's only job is to turn raw script text into a flat list of Tokens.
It does not understand grammar (e.g. "an investigation must contain braces").
That understanding belongs to the parser (next milestone).

Example:
    investigation "Test" {
        collect system_info;
    }

becomes tokens like:
    IDENT(investigation) STRING(Test) LBRACE IDENT(collect)
    IDENT(system_info) SEMICOLON RBRACE
"""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    IDENT = auto()      # words like: investigation, collect, system_info
    STRING = auto()      # "quoted text"
    LBRACE = auto()       # {
    RBRACE = auto()        # }
    SEMICOLON = auto()      # ;
    EOF = auto()              # marks the end of the token stream


@dataclass
class Token:
    type: TokenType
    value: str
    line: int  # which source line this token came from (helps error messages)


class LexError(Exception):
    """Raised when the lexer finds a character it does not recognize."""
    pass


# Characters that map directly to a single-character token type.
_SINGLE_CHAR_TOKENS = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ";": TokenType.SEMICOLON,
}


def tokenize(source: str) -> list[Token]:
    """
    Convert JOCKY source code into a list of Tokens.

    Raises LexError if an unrecognized character is encountered.
    """
    tokens: list[Token] = []
    line = 1
    i = 0
    length = len(source)

    while i < length:
        char = source[i]

        # Skip whitespace, tracking line numbers for error messages.
        if char == "\n":
            line += 1
            i += 1
            continue
        if char.isspace():
            i += 1
            continue

        # Skip single-line comments: // like this
        if char == "/" and i + 1 < length and source[i + 1] == "/":
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Single-character tokens: { } ;
        if char in _SINGLE_CHAR_TOKENS:
            tokens.append(Token(_SINGLE_CHAR_TOKENS[char], char, line))
            i += 1
            continue

        # String literals: "some text"
        if char == '"':
            start_line = line
            i += 1  # skip opening quote
            start = i
            while i < length and source[i] != '"':
                if source[i] == "\n":
                    line += 1
                i += 1
            if i >= length:
                raise LexError(f"Unterminated string starting at line {start_line}")
            value = source[start:i]
            i += 1  # skip closing quote
            tokens.append(Token(TokenType.STRING, value, start_line))
            continue

        # Identifiers/keywords: letters, digits, underscores (must start with a letter)
        if char.isalpha() or char == "_":
            start = i
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
            value = source[start:i]
            tokens.append(Token(TokenType.IDENT, value, line))
            continue

        raise LexError(f"Unrecognized character {char!r} at line {line}")

    tokens.append(Token(TokenType.EOF, "", line))
    return tokens