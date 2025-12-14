# Lexer/lexer.py
import ply.lex as lex
import re
import sys

# --- Reserved Keywords ---
reserved = {
    'func': 'FUNC', 'if': 'IF', 'elif': 'ELIF', 'else': 'ELSE', 'while': 'WHILE',
    'for': 'FOR', 'break': 'BREAK', 'continue': 'CONTINUE', 'int': 'INT',
    'float': 'FLOAT', 'bool': 'BOOL', 'char': 'CHAR', 'string': 'STRING',
    'return': 'RETURN', 'print': 'PRINT', 
    'Input': 'INPUT', 'input': 'INPUT',
    'false': 'FALSE', 'true': 'TRUE',
}

# --- Token List ---
tokens = [
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'CHAR_LITERAL',
    'STRING_LITERAL',
    'ID',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'LT', 'GT', 'LE', 'GE', 'EQ', 'NE',
    'NOT', 'OR', 'AND',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE', 'COMMA', 'SEMI', 'ASSIGN',
    'INVALID',
    'BAD_ID_WITH_DOLLAR' 
] + list(set(reserved.values()))

# --- Rules ---
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='
t_OR = r'\|\|'
t_AND = r'&&'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
t_LT = r'<'
t_GT = r'>'
t_NOT = r'!'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_SEMI = r';'
t_ASSIGN = r'='
t_ignore = ' \t'

def t_ignore_COMMENT_MULTI(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_ignore_COMMENT_SINGLE(t):
    r'//.*'

def _panic_mode(t):
    line_end = t.lexer.lexdata.find('\n', t.lexpos)
    if line_end == -1: line_end = len(t.lexer.lexdata)
    t.value = t.lexer.lexdata[t.lexpos:line_end]
    t.type = 'INVALID'
    delta = line_end - t.lexer.lexpos
    if delta > 0: t.lexer.skip(delta)
    return t

def t_FLOAT_LITERAL(t):
    r'[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+'
    return t

def t_INT_LITERAL(t):
    r'0x[0-9a-fA-F]+|[0-9]+[a-zA-Z0-9_]*'
    val = t.value
    if re.fullmatch(r'0x[0-9a-fA-F]+', val): return t
    if re.fullmatch(r'[0-9]+', val): return t
    return _panic_mode(t)

def t_BAD_ID_WITH_DOLLAR(t):
    r'[a-zA-Z0-9_]+\$[a-zA-Z0-9_$]*'
    return _panic_mode(t)

def t_CHAR_LITERAL(t):
    r"\'([^'\\]|\\.)\'"
    t.value = t.value[1:-1]
    return t

def t_STRING_LITERAL(t):
    r'\"([^"\\]|\\.)*\"'
    t.value = t.value[1:-1]
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    return _panic_mode(t)

# Build the lexer
lexer = lex.lex()
