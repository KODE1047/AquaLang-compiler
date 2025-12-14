# Parser/parser.py
import ply.yacc as yacc
import sys
import os

# Add the parent directory to sys.path to import Lexer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Lexer.lexer import tokens

# --- Precedence Table ---
precedence = (
    ('right', 'ASSIGN'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NE'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'NOT', 'UMINUS'),
)

# --- Grammar Rules ---

def p_program(p):
    '''program : declaration_list'''
    p[0] = ('program', p[1])

def p_declaration_list(p):
    '''declaration_list : declaration_list declaration
                        | declaration'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    '''declaration : var_decl
                   | func_decl
                   | error SEMI''' # <--- Global Error Recovery Here
    p[0] = p[1]

# --- Variables ---
# Removed 'error SEMI' from here to avoid conflicts
def p_var_decl(p):
    '''var_decl : type ID SEMI
                | type ID LBRACKET INT_LITERAL RBRACKET SEMI'''
    if len(p) == 4:
        p[0] = ('var_decl', p[1], p[2])
    else:
        p[0] = ('array_decl', p[1], p[2], p[4])

def p_type(p):
    '''type : INT
            | FLOAT
            | BOOL
            | CHAR
            | STRING'''
    p[0] = p[1]

# --- Functions ---
def p_func_decl(p):
    '''func_decl : FUNC ID LPAREN param_list_opt RPAREN block'''
    p[0] = ('func_decl', p[2], p[4], p[6])

def p_param_list_opt(p):
    '''param_list_opt : param_list
                      | empty'''
    p[0] = p[1]

def p_param_list(p):
    '''param_list : param_list COMMA param
                  | param'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_param(p):
    '''param : type ID'''
    p[0] = ('param', p[1], p[2])

# --- Blocks & Statements ---
def p_block(p):
    '''block : LBRACE statement_list RBRACE'''
    p[0] = ('block', p[2])

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | empty'''
    if len(p) == 3:
        if p[1] is None: p[1] = []
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_statement(p):
    '''statement : assignment_or_block
                 | var_decl
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | io_stmt SEMI
                 | return_stmt SEMI
                 | break_stmt SEMI
                 | continue_stmt SEMI
                 | error SEMI''' # <--- Local Error Recovery Here
    # This structure prevents reduce/reduce conflicts with var_decl
    p[0] = p[1]

def p_assignment_or_block(p):
    '''assignment_or_block : location ASSIGN expr semi_opt'''
    if p[4] is not None:
        p[0] = ('assign', p[1], p[3])
    else:
        p[0] = ('block_assign', p[1], p[3])

def p_location(p):
    '''location : ID
                | ID LBRACKET expr RBRACKET'''
    if len(p) == 2:
        p[0] = ('var', p[1])
    else:
        p[0] = ('index', p[1], p[3])

# --- Control Flow ---
def p_if_stmt(p):
    '''if_stmt : IF LPAREN expr RPAREN block elif_part else_part_opt'''
    p[0] = ('if', p[3], p[5], p[6], p[7])

def p_elif_part(p):
    '''elif_part : ELIF LPAREN expr RPAREN block elif_part
                 | empty'''
    if len(p) == 7:
        p[0] = [('elif', p[3], p[5])] + p[6]
    else:
        p[0] = []

def p_else_part_opt(p):
    '''else_part_opt : ELSE block
                     | empty'''
    if len(p) == 3:
        p[0] = ('else', p[2])
    else:
        p[0] = None

def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN expr RPAREN block'''
    p[0] = ('while', p[3], p[5])

def p_for_stmt(p):
    '''for_stmt : FOR LPAREN assignment SEMI expr SEMI assignment RPAREN block'''
    p[0] = ('for', p[3], p[5], p[7], p[9])

def p_assignment_pure(p):
    '''assignment : location ASSIGN expr'''
    p[0] = ('assign', p[1], p[3])

# --- I/O & Jumps ---
def p_io_stmt(p):
    '''io_stmt : PRINT LPAREN expr RPAREN
               | INPUT LPAREN ID RPAREN'''
    if p[1] == 'print':
        p[0] = ('print', p[3])
    else:
        p[0] = ('input', p[3])

def p_return_stmt(p):
    '''return_stmt : RETURN expr_opt'''
    p[0] = ('return', p[2])

def p_break_stmt(p):
    '''break_stmt : BREAK'''
    p[0] = ('break',)

def p_continue_stmt(p):
    '''continue_stmt : CONTINUE'''
    p[0] = ('continue',)

def p_expr_opt(p):
    '''expr_opt : expr
                | empty'''
    p[0] = p[1]

# --- Expressions ---
def p_expr_binop(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MOD expr
            | expr LT expr
            | expr GT expr
            | expr LE expr
            | expr GE expr
            | expr EQ expr
            | expr NE expr
            | expr OR expr
            | expr AND expr'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expr_unary(p):
    '''expr : MINUS expr %prec UMINUS
            | NOT expr'''
    p[0] = ('unary', p[1], p[2])

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]

def p_expr_literal(p):
    '''expr : literal'''
    p[0] = p[1]

def p_expr_location(p):
    '''expr : location'''
    p[0] = p[1]

def p_expr_funccall(p):
    '''expr : func_call'''
    p[0] = p[1]

def p_func_call(p):
    '''func_call : ID LPAREN arg_list_opt RPAREN'''
    p[0] = ('call', p[1], p[3])

def p_arg_list_opt(p):
    '''arg_list_opt : arg_list
                    | empty'''
    p[0] = p[1]

def p_arg_list(p):
    '''arg_list : arg_list COMMA expr
                | expr'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_literal(p):
    '''literal : INT_LITERAL
               | FLOAT_LITERAL
               | FALSE
               | TRUE
               | CHAR_LITERAL
               | STRING_LITERAL'''
    p[0] = ('literal', p[1])

# --- Helper Rules ---
def p_semi_opt(p):
    '''semi_opt : SEMI
                | empty'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = None

def p_empty(p):
    '''empty :'''
    pass

# --- Error Handling ---
def p_error(p):
    # Mark that an error occurred on the parser object
    parser.success = False
    
    if p:
        print(f"❌ Syntax Error at line {p.lineno}, token='{p.value}'")
    else:
        print("❌ Syntax Error at EOF (Unexpected end of input)")

# --- Build Parser ---
parser = yacc.yacc()
