# /Semantic/semantic.py
from Parser.ast import Node
from Semantic.symbol_table import SymbolTable

# --- Global State ---
symbol_table = SymbolTable()
error_list = []
current_func_ret_type = None # Tracks which function we are currently inside

def semantic_analysis(ast):
    """
    Main entry point.
    """
    # Reset State
    symbol_table.scopes = [{}]
    error_list.clear()
    global current_func_ret_type
    current_func_ret_type = None

    # Load built-in functions (print, input) if needed, or handle them as keywords
    # For now, we assume they are handled by statements, not func definitions.
    
    init(ast)
    return len(error_list) == 0

def init(ast):
    if ast:
        iterate(ast)
    print_errors()

def iterate(node):
    """
    Dispatcher: looks at node type and calls specific handler.
    """
    if not isinstance(node, Node):
        return

    # --- Declarations ---
    if node.type == 'var_decl':
        handle_var_decl(node)
    elif node.type == 'var_decl_array':
        handle_array_decl(node)
    elif node.type == 'func_decl':
        handle_func_decl(node)
    
    # --- Statements ---
    elif node.type == 'assign':
        handle_assignment(node)
    elif node.type == 'if':
        handle_if_stmt(node)
    elif node.type == 'while':
        handle_while_stmt(node)
    elif node.type == 'for':
        handle_for_stmt(node)
    elif node.type == 'return':
        handle_return(node)
    elif node.type == 'call':
        handle_func_call(node)
    
    # --- Blocks ---
    elif node.type == 'block':
        # Blocks (inside if/while) create new scopes
        symbol_table.enter_scope()
        for child in node.children:
            iterate(child)
        symbol_table.exit_scope()
        return # We iterated children manually, so return

    # --- Default Traversal ---
    # For nodes that don't need special handling but have children (like 'program')
    if hasattr(node, 'children') and node.children:
        for child in node.children:
            if isinstance(child, list): # Handle lists of nodes
                for item in child:
                    iterate(item)
            else:
                iterate(child)

# ----------------------------------------------------------------------
#                             Handlers
# ----------------------------------------------------------------------

def handle_var_decl(node):
    # structure: children=[type_node], leaf=ID
    var_type = node.children[0].leaf
    var_name = node.leaf
    
    if not symbol_table.define(var_name, var_type, "var"):
        error_list.append(f"Semantic Error: Variable '{var_name}' already declared in this scope.")

def handle_array_decl(node):
    # structure: children=[type_node, size_node], leaf=ID
    arr_type = node.children[0].leaf
    arr_size = node.children[1].leaf
    arr_name = node.leaf

    if not symbol_table.define(arr_name, arr_type, "array"):
        error_list.append(f"Semantic Error: Array '{arr_name}' already declared.")

def handle_func_decl(node):
    global current_func_ret_type
    
    # structure: func ID (params) block
    func_name = node.leaf
    
    # 1. Parse return type (AquaLang assumes 'void' if no explicit type? 
    # Actually your grammar doesn't show return type in decl! 
    # Wait, looking at grammar: func <id> (params) <block>.
    # It implies 'void' or inferred. Let's assume 'void' for now or generic.)
    # Note: Many C-like languages require type. AquaLang grammar in prompt is:
    # <func_decl> -> func <id> ( <param_list_opt> ) <block>
    # It seems strictly 'void' unless you intended to put type there.
    # **Correction**: Looking at your lexer, you have Types. But Func Decl has no type.
    # We will assume it is VOID or dynamic. Let's assume VOID for safety.
    ret_type = 'void' 

    if not symbol_table.define(func_name, ret_type, "func"):
        error_list.append(f"Semantic Error: Function '{func_name}' already declared.")
    
    # 2. Enter Function Scope
    symbol_table.enter_scope()
    current_func_ret_type = ret_type

    # 3. Handle Parameters
    params_node = node.children[0] # params node
    param_types = []
    
    if params_node and params_node.children:
        for param in params_node.children:
            # param -> type ID
            p_type = param.children[0].leaf
            p_name = param.leaf
            param_types.append(p_type)
            symbol_table.define(p_name, p_type, "var")

    # Update function symbol with param types (for checking calls later)
    # We cheat and update the parent scope's entry
    func_entry = symbol_table.scopes[-2][func_name]
    func_entry['param_types'] = param_types

    # 4. Process Body
    body_node = node.children[1]
    # We iterate body manually to avoid creating *another* scope 
    # (since func decl already made one)
    if body_node.children:
        for stmt in body_node.children:
            iterate(stmt)

    symbol_table.exit_scope()
    current_func_ret_type = None

def handle_assignment(node):
    # children=[location, expr]
    loc_node = node.children[0]
    expr_node = node.children[1]

    # 1. Get LHS Type
    lhs_name = loc_node.leaf
    lhs_symbol = symbol_table.lookup(lhs_name)
    
    if not lhs_symbol:
        error_list.append(f"Semantic Error: Variable '{lhs_name}' not declared.")
        return

    lhs_type = lhs_symbol['type']
    
    # 2. Check Array Indexing (if array access)
    if loc_node.type == 'array_access':
        index_expr = loc_node.children[0]
        idx_type = get_expr_type(index_expr)
        if idx_type != 'int':
            error_list.append(f"Semantic Error: Array index must be 'int', got '{idx_type}'.")
        # Note: If it's an array access, the resulting type is the base type (e.g., int arr[] -> int)
        # So lhs_type is correct.

    # 3. Get RHS Type
    rhs_type = get_expr_type(expr_node)

    # 4. Compatibility Check
    if not check_type_compatibility(lhs_type, rhs_type):
        error_list.append(f"Type Mismatch: Cannot assign '{rhs_type}' to '{lhs_type}'.")

def handle_if_stmt(node):
    # children=[condition, block, (elif...), (else...)]
    cond_expr = node.children[0]
    cond_type = get_expr_type(cond_expr)
    
    if cond_type != 'bool':
        error_list.append(f"Semantic Error: 'if' condition must be boolean. Got '{cond_type}'.")
    
    # Process blocks
    for child in node.children[1:]:
        iterate(child)

def handle_while_stmt(node):
    cond_expr = node.children[0]
    cond_type = get_expr_type(cond_expr)
    
    if cond_type != 'bool':
        error_list.append(f"Semantic Error: 'while' condition must be boolean.")
    
    iterate(node.children[1]) # Block

def handle_for_stmt(node):
    # for (assign; expr; assign) block
    # children=[assign1, expr, assign2, block]
    
    # 1. Check init assignment
    iterate(node.children[0]) 
    
    # 2. Check condition
    cond_type = get_expr_type(node.children[1])
    if cond_type != 'bool':
        error_list.append(f"Semantic Error: 'for' condition must be boolean.")

    # 3. Check update assignment
    iterate(node.children[2])

    # 4. Block
    iterate(node.children[3])

def handle_return(node):
    # children=[expr] or empty
    if not current_func_ret_type:
        error_list.append("Semantic Error: 'return' statement outside of function.")
        return

    if node.children:
        ret_expr_type = get_expr_type(node.children[0])
        if not check_type_compatibility(current_func_ret_type, ret_expr_type):
            error_list.append(f"Return Type Mismatch: Expected '{current_func_ret_type}', got '{ret_expr_type}'.")
    else:
        # return; -> implies void
        if current_func_ret_type != 'void':
             error_list.append(f"Return Type Mismatch: Expected '{current_func_ret_type}', got 'void'.")

def handle_func_call(node):
    func_name = node.leaf
    func_symbol = symbol_table.lookup(func_name)
    
    if not func_symbol:
        error_list.append(f"Semantic Error: Function '{func_name}' not defined.")
        return

    if func_symbol['category'] != 'func':
        error_list.append(f"Semantic Error: '{func_name}' is not a function.")
        return

    # Check arguments
    # defined params
    defined_params = func_symbol.get('param_types', [])
    
    # passed args
    args_node = node.children[0] # args node
    passed_args = args_node.children if args_node else []
    
    if len(defined_params) != len(passed_args):
        error_list.append(f"Argument Count Mismatch: '{func_name}' expects {len(defined_params)} args, got {len(passed_args)}.")
        return

    for i, (def_type, arg_expr) in enumerate(zip(defined_params, passed_args)):
        arg_type = get_expr_type(arg_expr)
        if not check_type_compatibility(def_type, arg_type):
             error_list.append(f"Argument {i+1} Mismatch: Expected '{def_type}', got '{arg_type}'.")


# ----------------------------------------------------------------------
#                             Helpers
# ----------------------------------------------------------------------

def get_expr_type(node):
    """
    Recursively determines type of an expression.
    """
    if not isinstance(node, Node):
        return 'void'

    # 1. Literals
    if node.type == 'literal':
        val = node.leaf
        if isinstance(val, bool) or str(val) in ['true', 'false']: return 'bool'
        if isinstance(val, int): return 'int'
        if isinstance(val, float): return 'float'
        if isinstance(val, str): 
            if val.startswith("'"): return 'char'
            if val.startswith('"'): return 'string'
            # Check if it looks like int/float string
            if '.' in str(val): return 'float'
            return 'int'
            
    # 2. Identifiers (Variables)
    elif node.type == 'id':
        sym = symbol_table.lookup(node.leaf)
        if not sym:
            error_list.append(f"Semantic Error: Variable '{node.leaf}' used before declaration.")
            return 'error'
        return sym['type']

    elif node.type == 'array_access':
        sym = symbol_table.lookup(node.leaf)
        if not sym: return 'error'
        return sym['type'] # Returns base type

    # 3. Binary Operations
    elif node.type == 'bin_op':
        left = get_expr_type(node.children[0])
        right = get_expr_type(node.children[1])
        op = node.leaf

        if left == 'error' or right == 'error': return 'error'

        # Arithmetic
        if op in ['+', '-', '*', '/', '%']:
            if left == 'int' and right == 'int': return 'int'
            if (left == 'float' or right == 'float') and (left in ['int', 'float'] and right in ['int', 'float']):
                return 'float' # Coercion
            error_list.append(f"Type Error: Invalid operands for '{op}': {left}, {right}")
            return 'error'

        # Relational (Always bool)
        if op in ['<', '>', '<=', '>=', '==', '!=']:
            if check_type_compatibility(left, right) or check_type_compatibility(right, left):
                return 'bool'
            error_list.append(f"Type Error: Cannot compare {left} and {right}")
            return 'error'

        # Logical
        if op in ['&&', '||']:
            if left == 'bool' and right == 'bool': return 'bool'
            error_list.append("Type Error: Logical operators require boolean operands.")
            return 'error'

    # 4. Unary
    elif node.type == 'unary_op':
        child = get_expr_type(node.children[0])
        op = node.leaf
        if op == '!':
            if child == 'bool': return 'bool'
        elif op == '-':
            if child in ['int', 'float']: return child
        return 'error'
    
    # 5. Function Calls (in expr)
    elif node.type == 'call':
        # Reuse handle_func_call logic? 
        # Ideally, we should unify this. 
        # For now, simplistic lookup:
        sym = symbol_table.lookup(node.leaf)
        if sym: return 'void' # or whatever we decided func return type is

    return 'unknown'

def check_type_compatibility(target, source):
    """
    Can 'source' be assigned to 'target'?
    """
    if target == source: return True
    if target == 'float' and source == 'int': return True # Implicit Int -> Float
    return False

def print_errors():
    for err in error_list:
        print(f"\033[91m{err}\033[0m")

# ----------------------------------------------------------------------
#                             Reporting Tools
# ----------------------------------------------------------------------

def get_semantic_analysis_report():
    """
    Returns a string summary of errors and the final state of the Symbol Table.
    """
    report = []
    
    # 1. Report Errors
    if error_list:
        report.append("\n❌ SEMANTIC ERRORS:")
        for err in error_list:
            report.append(f" - {err}")
    else:
        report.append("\n✅ Semantic Check Passed: No errors.")

    # 2. Report Symbol Table (Global Scope)
    # Note: After analysis, only Global Scope remains in the stack.
    report.append("\n📊 SYMBOL TABLE (Global Scope Only):")
    report.append("-" * 50)
    report.append(f"{'Identifier':<20} {'Type':<10} {'Category':<10}")
    report.append("-" * 50)
    
    # We access the symbol_table instance's scopes directly
    if symbol_table.scopes:
        global_scope = symbol_table.scopes[0]
        for name, info in global_scope.items():
            report.append(f"{name:<20} {info['type']:<10} {info['category']:<10}")
    
    report.append("-" * 50)
    return "\n".join(report)

def print_symbol_table():
    """
    Helper to print directly to console (optional usage).
    """
    print(get_semantic_analysis_report())