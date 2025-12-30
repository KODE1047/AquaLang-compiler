# /Parser/parser.py

import ply.yacc as yacc
from Lexer.lexer import tokens
from Parser.ast import Node  # <--- UPDATED IMPORT

# --- Precedence & Associativity ---
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NE'),
    ('nonassoc', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'NOT', 'UMINUS'),
)

# --- Grammar Rules ---

def p_program(p):
    '''program : declaration_list'''
    p[0] = Node('program', children=p[1])

def p_declaration_list(p):
    '''declaration_list : declaration_list declaration
                        | declaration'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    '''declaration : var_decl
                   | func_decl'''
    p[0] = p[1]

# --- Variable Declaration ---
def p_var_decl_scalar(p):
    '''var_decl : type ID SEMI'''
    p[0] = Node('var_decl', children=[p[1]], leaf=p[2])

def p_var_decl_array(p):
    '''var_decl : type ID LBRACKET INT_LITERAL RBRACKET SEMI'''
    size_node = Node('size', leaf=p[4])
    p[0] = Node('var_decl_array', children=[p[1], size_node], leaf=p[2])

def p_type(p):
    '''type : INT
            | FLOAT
            | BOOL
            | CHAR
            | STRING'''
    p[0] = Node('type', leaf=p[1])

# --- Function Declaration ---
def p_func_decl(p):
    '''func_decl : FUNC ID LPAREN param_list_opt RPAREN block'''
    p[0] = Node('func_decl', children=[p[4], p[6]], leaf=p[2])

def p_param_list_opt(p):
    '''param_list_opt : param_list
                      | empty'''
    p[0] = Node('params', children=p[1]) if p[1] else Node('params')

def p_param_list(p):
    '''param_list : param_list COMMA param
                  | param'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_param(p):
    '''param : type ID'''
    p[0] = Node('param', children=[p[1]], leaf=p[2])

# --- Block & Statements ---
def p_block(p):
    '''block : LBRACE statement_list RBRACE'''
    p[0] = Node('block', children=p[2])

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_statement(p):
    '''statement : assignment SEMI
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | io_stmt SEMI
                 | return_stmt SEMI
                 | break_stmt SEMI
                 | continue_stmt SEMI
                 | block'''
    p[0] = p[1]

# --- Assignment ---
def p_assignment(p):
    '''assignment : location ASSIGN expr'''
    p[0] = Node('assign', children=[p[1], p[3]])

def p_location_id(p):
    '''location : ID'''
    p[0] = Node('id', leaf=p[1])

def p_location_array(p):
    '''location : ID LBRACKET expr RBRACKET'''
    p[0] = Node('array_access', children=[p[3]], leaf=p[1])

# --- Control Flow: IF ---
def p_if_stmt(p):
    '''if_stmt : IF LPAREN expr RPAREN block elif_part else_part_opt'''
    children = [p[3], p[5]] # Condition, Then-Block
    if p[6]: children.append(p[6]) # Elif
    if p[7]: children.append(p[7]) # Else
    p[0] = Node('if', children=children)

def p_elif_part(p):
    '''elif_part : ELIF LPAREN expr RPAREN block elif_part
                 | empty'''
    if len(p) == 7:
        children = [p[3], p[5]]
        if p[6]: children.append(p[6])
        p[0] = Node('elif', children=children)
    else:
        p[0] = None

def p_else_part_opt(p):
    '''else_part_opt : ELSE block
                     | empty'''
    if len(p) == 3:
        p[0] = Node('else', children=[p[2]])
    else:
        p[0] = None

# --- Control Flow: Loops ---
def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN expr RPAREN block'''
    p[0] = Node('while', children=[p[3], p[5]])

def p_for_stmt(p):
    '''for_stmt : FOR LPAREN assignment SEMI expr SEMI assignment RPAREN block'''
    p[0] = Node('for', children=[p[3], p[5], p[7], p[9]])

# --- IO Statements ---
def p_io_stmt_print(p):
    '''io_stmt : PRINT LPAREN expr RPAREN'''
    p[0] = Node('print', children=[p[3]])

def p_io_stmt_input(p):
    '''io_stmt : INPUT LPAREN ID RPAREN'''
    p[0] = Node('input', leaf=p[3])

# --- Jump Statements ---
def p_return_stmt(p):
    '''return_stmt : RETURN expr_opt'''
    p[0] = Node('return', children=[p[2]]) if p[2] else Node('return')

def p_expr_opt(p):
    '''expr_opt : expr
                | empty'''
    p[0] = p[1]

def p_break_stmt(p):
    '''break_stmt : BREAK'''
    p[0] = Node('break')

def p_continue_stmt(p):
    '''continue_stmt : CONTINUE'''
    p[0] = Node('continue')

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
            | expr AND expr
            | expr OR expr'''
    p[0] = Node('bin_op', children=[p[1], p[3]], leaf=p[2])

def p_expr_unary(p):
    '''expr : MINUS expr %prec UMINUS
            | NOT expr'''
    p[0] = Node('unary_op', children=[p[2]], leaf=p[1])

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]

def p_expr_literal(p):
    '''expr : literal'''
    p[0] = p[1]

def p_expr_location(p):
    '''expr : location'''
    p[0] = p[1]

def p_expr_call(p):
    '''expr : func_call'''
    p[0] = p[1]

# --- Function Calls ---
def p_func_call(p):
    '''func_call : ID LPAREN arg_list_opt RPAREN'''
    p[0] = Node('call', children=[p[3]], leaf=p[1])

def p_arg_list_opt(p):
    '''arg_list_opt : arg_list
                    | empty'''
    p[0] = Node('args', children=p[1]) if p[1] else Node('args')

def p_arg_list(p):
    '''arg_list : arg_list COMMA expr
                | expr'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# --- Literals ---
def p_literal(p):
    '''literal : INT_LITERAL
               | FLOAT_LITERAL
               | CHAR_LITERAL
               | STRING_LITERAL'''
    p[0] = Node('literal', leaf=p[1])

def p_literal_bool(p):
    '''literal : TRUE
               | FALSE'''
    p[0] = Node('literal', leaf=p[1])

# --- Helpers ---
def p_empty(p):
    '''empty :'''
    pass

def p_error(t):
    if t:
        print(f"Syntax error at line {t.lineno}, position {t.lexpos}: Unexpected token '{t.value}'")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()