import ply.lex as lex
import argparse
import shutil
import os
from collections import Counter

# --- Reserved Keywords ---
# Map of reserved keyword strings to their token types
reserved = {
    'func': 'FUNC',
    'if': 'IF',
    'elif': 'ELIF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'char': 'CHAR',
    'string': 'STRING',
    'return': 'RETURN',
    'print': 'PRINT',
    'input': 'INPUT',
    'false': 'FALSE',
    'true': 'TRUE',
}

# --- Token List ---
# List of all token names, including those from the reserved map
tokens = [
    # Literals
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'CHAR_LITERAL',
    'STRING_LITERAL',

    # Identifier
    'ID',

    # Operators
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'LT', 'GT', 'LE', 'GE', 'EQ', 'NE',
    'NOT', 'OR', 'AND',

    # Separators / Grouping
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'SEMI',
    'ASSIGN',
] + list(reserved.values())

# --- Simple Token Rules (Operators & Separators) ---
# Multi-character operators MUST be defined before single-character ones

# Relational / Equality
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='

# Logical
t_OR = r'\|\|'
t_AND = r'&&'

# Arithmetic
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

# Relational
t_LT = r'<'
t_GT = r'>'

# Logical
t_NOT = r'!'

# Separators / Grouping
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_SEMI = r';'
t_ASSIGN = r'='

# --- Ignored Rules (Whitespace & Comments) ---

# Ignore space and tab
t_ignore = ' \t'

# Ignore multi-line C-style comments
def t_ignore_COMMENT_MULTI(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')  # Count newlines in comment
    pass  # Discard the token

# Ignore single-line C++-style comments
def t_ignore_COMMENT_SINGLE(t):
    r'//.*'
    pass  # Discard the token

# --- Complex Token Rules (Literals & ID) ---

# Matches: 123.45, 123.45e-6, 123e6
def t_FLOAT_LITERAL(t):
    r'[0-9]+\.[0-9]+([eE][+-]?[0-9]+)? | [0-9]+[eE][+-]?[0-9]+'
    return t

# Matches: 0xABC, 123
def t_INT_LITERAL(t):
    r'0x[0-9a-fA-F]+ | [0-9]+'
    return t

# Matches: 'a', '\n', '\''
def t_CHAR_LITERAL(t):
    r"\'([^'\\] | \\.)\'"
    t.value = t.value[1:-1]  # Remove surrounding quotes
    return t

# Matches: "hello", "line\n", "quote\""
def t_STRING_LITERAL(t):
    r'\"([^"\\] | \\.)*\"'
    t.value = t.value[1:-1]  # Remove surrounding quotes
    return t

# Identifiers (and Keyword Check)
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if the identifier is a reserved keyword
    t.type = reserved.get(t.value, 'ID')
    return t

# --- Line Number Tracking ---
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# --- Error Handling ---
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# --- Build the Lexer ---
lexer = lex.lex()

# --- Test Harness ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AquaLang lexer tester with pretty output')
    parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in output')
    parser.add_argument('--summary', action='store_true', help='Show a summary count of token types at the end')
    args = parser.parse_args()

    # Colorize text 
    def _color(text, code, enable=True):
        if not enable:
            return str(text)
        return f"\033[{code}m{text}\033[0m"

    def _format_value(val):
        s = repr(val) if not isinstance(val, str) else val
        s = s.replace('\n', '\\n')
        max_len = 40
        if len(s) > max_len:
            return s[:max_len-3] + '...'
        return s

    def pretty_print(tokens, use_color=True, show_summary=False):
        term_w = shutil.get_terminal_size((80, 20)).columns
        idx_w = max(3, len(str(len(tokens))))
        type_w = max(6, max((len(t['type']) for t in tokens), default=6))
        line_w = max(4, max((len(str(t['line'])) for t in tokens), default=4))

        other = idx_w + type_w + line_w + 20  
        value_w = max(10, term_w - other)

        sep = '+' + '-'*(idx_w+2) + '+' + '-'*(type_w+2) + '+' + '-'*(value_w+2) + '+' + '-'*(line_w+2) + '+'

        header = (
            f"| {'#'.ljust(idx_w)} | {'Type'.ljust(type_w)} | {'Value'.ljust(value_w)} | {'Ln'.ljust(line_w)} |"
        )

        print(_color(sep, '90', use_color))
        print(_color(header, '1;37', use_color))
        print(_color(sep, '90', use_color))

        for i, t in enumerate(tokens, start=1):
            type_col = _color(t['type'].ljust(type_w), '36', use_color)
            val_col = _color(_format_value(t['value']).ljust(value_w), '32', use_color)
            line_col = _color(str(t['line']).rjust(line_w), '33', use_color)
            idx_col = _color(str(i).rjust(idx_w), '90', use_color)
            print(f"| {idx_col} | {type_col} | {val_col} | {line_col} |")

        print(_color(sep, '90', use_color))

        if show_summary:
            counts = Counter(t['type'] for t in tokens)
            print('\nToken summary:')
            for tok_type, cnt in counts.most_common():
                print(f"  {tok_type:20} {cnt}")

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'input.txt')
        with open(file_path, 'r') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"Error: input.txt file not found at {file_path}")
        exit(1)
    except IOError:
        print(f"Error: Could not read input.txt file at {file_path}")
        exit(1)

    # Lexems
    lexer.input(data)

    # Better output formatting
    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_list.append({
            'type': tok.type,
            'value': tok.value,
            'line': tok.lineno,
            'lexpos': getattr(tok, 'lexpos', None),
        })

    print(_color('--- AquaLang Lexer Output ---', '1;37', not args.no_color))
    pretty_print(token_list, use_color=not args.no_color, show_summary=args.summary)
    print(_color('--- End of Output ---', '1;37', not args.no_color))