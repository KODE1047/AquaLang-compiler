import ply.lex as lex
import argparse
import shutil
import os
from collections import Counter

# --- Reserved Keywords ---
# (Same as your provided code)
reserved = {
    'func': 'FUNC', 'if': 'IF', 'elif': 'ELIF', 'else': 'ELSE', 'while': 'WHILE',
    'for': 'FOR', 'break': 'BREAK', 'continue': 'CONTINUE', 'int': 'INT',
    'float': 'FLOAT', 'bool': 'BOOL', 'char': 'CHAR', 'string': 'STRING',
    'return': 'RETURN', 'print': 'PRINT', 'input': 'INPUT', 'false': 'FALSE',
    'true': 'TRUE',
}

# --- Token List ---
# MODIFIED: Added 'INVALID' token
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
    
    # Error Token
    'INVALID',  # <-- NEW TOKEN ADDED HERE
] + list(reserved.values())

# --- Simple Token Rules (Operators & Separators) ---
# (Same as your provided code)
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

# --- Ignored Rules (Whitespace & Comments) ---
# (Same as your provided code)
t_ignore = ' \t'

def t_ignore_COMMENT_MULTI(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_ignore_COMMENT_SINGLE(t):
    r'//.*'
    pass

# --- Complex Token Rules (Literals & ID) ---
# (Same as your provided code)
def t_FLOAT_LITERAL(t):
    r'[0-9]+\.[0-9]+([eE][+-]?[0-9]+)? | [0-9]+[eE][+-]?[0-9]+'
    return t

def t_INT_LITERAL(t):
    r'0x[0-9a-fA-F]+ | [0-9]+'
    return t

def t_CHAR_LITERAL(t):
    r"\'([^'\\] | \\.)\'"
    t.value = t.value[1:-1]
    return t

def t_STRING_LITERAL(t):
    r'\"([^"\\] | \\.)*\"'
    t.value = t.value[1:-1]
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# --- Line Number Tracking ---
# (Same as your provided code)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# --- Error Handling ---
# MODIFIED: This function now implements your "capture the line" logic
def t_error(t):
    # Find the start of the current line
    line_start_pos = t.lexer.lexdata.rfind('\n', 0, t.lexpos) + 1
    
    # Find the end of the current line
    line_end_pos = t.lexer.lexdata.find('\n', t.lexpos)
    if line_end_pos == -1:
        # Reached end of file
        line_end_pos = len(t.lexer.lexdata)

    # The value of the token is the entire line's content
    line_content = t.lexer.lexdata[line_start_pos:line_end_pos]
    
    # How many characters to skip to get to the *end* of this line
    skip_len = line_end_pos - t.lexpos
    
    # Report the error
    print(f"Lexical Error: Invalid line (char '{t.value[0]}') at line {t.lexer.lineno}. Skipping line.")

    # Create the new INVALID token
    t.type = 'INVALID'
    t.value = line_content
    
    # Skip the rest of the line and return the token
    t.lexer.skip(skip_len)
    return t

# --- Build the Lexer ---
# (Same as your provided code)
lexer = lex.lex()

# --- Test Harness ---
# (Same as your provided code)
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
        
        # --- Handle INVALID token coloring ---
        # Find the max width, *excluding* potentially long INVALID tokens
        non_invalid_tokens = [t for t in tokens if t['type'] != 'INVALID']
        
        idx_w = max(3, len(str(len(tokens))))
        type_w = max(7, max((len(t['type']) for t in tokens), default=7)) # 7 for 'INVALID'
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
            
            val_str = _format_value(t['value'])
            
            # --- Special coloring for INVALID tokens ---
            if t['type'] == 'INVALID':
                type_col = _color(t['type'].ljust(type_w), '1;31', use_color) # Bright Red
                val_col = _color(val_str.ljust(value_w), '31', use_color) # Red
            else:
                type_col = _color(t['type'].ljust(type_w), '36', use_color) # Cyan
                val_col = _color(val_str.ljust(value_w), '32', use_color) # Green
            
            line_col = _color(str(t['line']).rjust(line_w), '33', use_color)
            idx_col = _color(str(i).rjust(idx_w), '90', use_color)
            
            print(f"| {idx_col} | {type_col} | {val_col} | {line_col} |")

        print(_color(sep, '90', use_color))

        if show_summary:
            counts = Counter(t['type'] for t in tokens)
            print('\nToken summary:')
            for tok_type, cnt in counts.most_common():
                color_code = '1;31' if tok_type == 'INVALID' else '37'
                tok_name = _color(tok_type, color_code, use_color)
                print(f"  {tok_name:30} {cnt}")

    try:
        #--------------------------------- test file ---------------------------------
        test_file = 'test1.txt'
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_file)
        with open(file_path, 'r') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"Error: {test_file} file not found at {file_path}")
        exit(1)
    except IOError:
        print(f"Error: Could not read {test_file} file at {file_path}")
        exit(1)
    except NameError: # Handle case where __file__ is not defined (e.g., in REPL)
        print("Error: Could not determine file path. Is this running as a script?")
        data = "int a = 0x; // This will fail" # Fallback data
        

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