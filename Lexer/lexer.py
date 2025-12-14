# /Lexer/lexer.py
import ply.lex as lex
import argparse
import shutil
import os
import re
from collections import Counter

# --- Reserved Keywords ---
reserved = {
    'func': 'FUNC', 'if': 'IF', 'elif': 'ELIF', 'else': 'ELSE', 'while': 'WHILE',
    'for': 'FOR', 'break': 'BREAK', 'continue': 'CONTINUE', 'int': 'INT',
    'float': 'FLOAT', 'bool': 'BOOL', 'char': 'CHAR', 'string': 'STRING',
    'return': 'RETURN', 'print': 'PRINT', 
    'Input': 'INPUT', 'input': 'INPUT', # Handles both cases for safety
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
] + list(set(reserved.values())) # Use set to avoid duplicate values

# --- Simple Token Rules ---
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

# --- Comments ---
def t_ignore_COMMENT_MULTI(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_ignore_COMMENT_SINGLE(t):
    r'//.*'

# --- 🚨 HELPER: Panic Mode ---
def _panic_mode(t):
    line_end = t.lexer.lexdata.find('\n', t.lexpos)
    if line_end == -1:
        line_end = len(t.lexer.lexdata)
    
    t.value = t.lexer.lexdata[t.lexpos:line_end]
    t.type = 'INVALID'
    
    delta = line_end - t.lexer.lexpos
    if delta > 0:
        t.lexer.skip(delta)
    
    return t

# --- ⚠️ Critical: Regex Priority ---

# 1. FLOAT LITERAL (Strict Priority)
def t_FLOAT_LITERAL(t):
    r'[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+'
    return t

# 2. MASTER NUMERIC DISPATCHER
def t_INT_LITERAL(t):
    r'0x[0-9a-fA-F]+|[0-9]+[a-zA-Z0-9_]*'
    
    val = t.value
    if re.fullmatch(r'0x[0-9a-fA-F]+', val):
        return t
    if re.fullmatch(r'[0-9]+', val):
        return t
    return _panic_mode(t)

# 3. BAD ID WITH DOLLAR
def t_BAD_ID_WITH_DOLLAR(t):
    r'[a-zA-Z0-9_]+\$[a-zA-Z0-9_$]*'
    return _panic_mode(t)

# 4. CHAR/STRING
def t_CHAR_LITERAL(t):
    r"\'([^'\\]|\\.)\'"
    t.value = t.value[1:-1]
    return t

def t_STRING_LITERAL(t):
    r'\"([^"\\]|\\.)*\"'
    t.value = t.value[1:-1]
    return t

# 5. ID (Standard)
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# --- Line Number Tracking ---
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# --- Error Handling ---
def t_error(t):
    return _panic_mode(t)

# --- Build Lexer ---
lexer = lex.lex()

# --- Test Harness ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AquaLang lexer tester')
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()

    def _color(text, code, enable=True):
        return f"\033[{code}m{text}\033[0m" if enable else str(text)

    def _format_value(val):
        s = repr(val) if not isinstance(val, str) else val
        return (s[:47] + '...') if len(s) > 50 else s

    def pretty_print(tokens, use_color=True, show_summary=False):
        term_w = shutil.get_terminal_size((80, 20)).columns
        idx_w, type_w, line_w = 3, 15, 4
        other_w = idx_w + type_w + line_w + 13
        value_w = max(10, term_w - other_w)
        
        sep = f"+{'-'*(idx_w+2)}+{'-'*(type_w+2)}+{'-'*(value_w+2)}+{'-'*(line_w+2)}+"
        header = f"| {'#':<{idx_w}} | {'Type':<{type_w}} | {'Value':<{value_w}} | {'Ln':<{line_w}} |"
        
        print(_color(sep, '90', use_color))
        print(_color(header, '1;37', use_color))
        print(_color(sep, '90', use_color))

        for i, t in enumerate(tokens, start=1):
            val_str = _format_value(t['value'])
            
            if t['type'] == 'INVALID':
                type_col = _color(t['type'].ljust(type_w), '1;31', use_color) 
                val_col = _color(val_str.ljust(value_w), '31', use_color)
            else:
                type_col = _color(t['type'].ljust(type_w), '36', use_color)
                val_col = _color(val_str.ljust(value_w), '32', use_color)
            
            idx_col = _color(str(i).rjust(idx_w), '90', use_color)
            line_col = _color(str(t['line']).rjust(line_w), '33', use_color)

            print(f"| {idx_col} | {type_col} | {val_col} | {line_col} |")
        
        print(_color(sep, '90', use_color))

        if show_summary:
            counts = Counter(t['type'] for t in tokens)
            print('\nToken summary:')
            for tok_type, cnt in counts.most_common():
                color_code = '1;31' if tok_type == 'INVALID' else '37'
                print(f"  {_color(tok_type, color_code, use_color):30} {cnt}")

    try:
        test_file = 'test1.txt'
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_file)
        with open(file_path, 'r') as file:
            data = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

    lexer.input(data)

    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        
        token_list.append({
            'type': tok.type,
            'value': tok.value,
            'line': tok.lineno,
        })
        
        # --- STOP ON FIRST ERROR ---
        if tok.type == 'INVALID':
            break

    print(_color('--- AquaLang Lexer Output ---', '1;37', not args.no_color))
    pretty_print(token_list, use_color=not args.no_color, show_summary=args.summary)
    print(_color('--- End of Output ---', '1;37', not args.no_color))
