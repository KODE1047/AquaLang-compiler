# /CodeGen/codegeneration.py
from Parser.ast import Node

class CodeGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.temp_counter = 0
        self.label_counter = 0
        
        # Result Storage
        self.data_section = []   # For declarations: x DW ?
        self.code_section = []   # For instructions: ADD a, b, t1
        self.errors = []
        
        # Start Generation
        if ast:
            self.generate(ast)

    # --- Helpers ---
    def new_temp(self):
        """Allocates a new temporary variable (t0, t1, ...)"""
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self):
        """Generates a new jump label (L1, L2, ...)"""
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, op, arg1, arg2, result):
        """Appends a 3-Address Code instruction"""
        # Format: (OP, ARG1, ARG2, RES)
        # We store it as a formatted string for display
        instr = f"\t{op}\t{arg1}, {arg2}, {result}"
        self.code_section.append(instr)

    def emit_label(self, label):
        self.code_section.append(f"{label}:")

    def add_var_decl(self, name, var_type):
        """Adds variable to data section"""
        size = 'DW' if var_type == 'int' else 'DB' # Simplified size
        self.data_section.append(f"\t{name}\t{size}\t?")

    # --- Traversal ---
    def generate(self, node):
        if not isinstance(node, Node):
            return

        method_name = f'gen_{node.type}'
        visitor = getattr(self, method_name, self.gen_children)
        return visitor(node)

    def gen_children(self, node):
        if node.children:
            for child in node.children:
                # Handle lists of nodes (like statement lists)
                if isinstance(child, list):
                    for item in child:
                        self.generate(item)
                else:
                    self.generate(child)

    # --- Program Structure ---
    def gen_program(self, node):
        # node.children is a list of declarations
        for decl in node.children:
            self.generate(decl)

    def gen_var_decl(self, node):
        # structure: children=[type], leaf=name
        var_type = node.children[0].leaf
        var_name = node.leaf
        self.add_var_decl(var_name, var_type)

    def gen_func_decl(self, node):
        # func name(params) block
        func_name = node.leaf
        self.emit_label(f"FUNC_{func_name}")
        
        # Parameters would be popped from stack here in a real compiler
        # For TAC, we assume they are available or handled by activation records
        
        # Body
        block_node = node.children[1]
        self.generate(block_node)
        
        # Implicit Return
        self.emit('RET', '', '', '')

    def gen_block(self, node):
        # Just visit statements
        for stmt in node.children:
            self.generate(stmt)

    # --- Statements ---
    def gen_assign(self, node):
        # structure: location = expr
        target_node = node.children[0]
        expr_node = node.children[1]

        # 1. Evaluate Expression -> returns temp var holding result
        result_temp = self.gen_expr(expr_node)

        # 2. Handle Target
        if target_node.type == 'array_access':
            # arr[idx] = val  =>  MOV val, arr[idx] (Abstracted)
            array_name = target_node.leaf
            idx_expr = self.gen_expr(target_node.children[0])
            self.emit('ASTORE', result_temp, idx_expr, array_name) # Array Store
        else:
            # x = val
            var_name = target_node.leaf
            self.emit('MOV', result_temp, '', var_name)

    def gen_if(self, node):
        # children: [cond, block, (elif...), (else...)]
        cond_node = node.children[0]
        true_block = node.children[1]
        
        # Labels
        label_false = self.new_label() # Jump here if condition is false
        label_exit = self.new_label()  # Jump here after finishing true block

        # 1. Condition
        cond_temp = self.gen_expr(cond_node)
        self.emit('JPF', cond_temp, label_false, '') # Jump If False

        # 2. True Block
        self.generate(true_block)
        self.emit('JMP', label_exit, '', '')

        # 3. Handle Elif/Else logic
        self.emit_label(label_false)
        
        # Check if we have elif/else nodes in children
        # Note: Your AST might nest them or list them. 
        # Assuming list based on your grammar logic:
        # If there are more children, they are elif/else parts
        
        current_child_idx = 2
        while current_child_idx < len(node.children):
            child = node.children[current_child_idx]
            if not child: break
            
            if child.type == 'elif':
                # Elif logic: Label -> Cond -> JPF Next -> Body -> JMP Exit
                next_elif = self.new_label()
                elif_cond = self.gen_expr(child.children[0])
                self.emit('JPF', elif_cond, next_elif, '')
                
                self.generate(child.children[1]) # Body
                self.emit('JMP', label_exit, '', '')
                
                self.emit_label(next_elif)
            
            elif child.type == 'else':
                self.generate(child.children[0]) # Else Body
            
            current_child_idx += 1

        self.emit_label(label_exit)

    def gen_while(self, node):
        # while (cond) block
        label_start = self.new_label()
        label_end = self.new_label()

        self.emit_label(label_start)
        
        # Condition
        cond_temp = self.gen_expr(node.children[0])
        self.emit('JPF', cond_temp, label_end, '')

        # Body
        self.generate(node.children[1])
        self.emit('JMP', label_start, '', '')

        self.emit_label(label_end)

    def gen_for(self, node):
        # for (assign1; cond; assign2) block
        # Desugar to:
        # assign1
        # START:
        # if !cond jump END
        # block
        # assign2
        # jump START
        # END:
        
        label_start = self.new_label()
        label_end = self.new_label()

        # 1. Initialization
        self.generate(node.children[0])

        self.emit_label(label_start)

        # 2. Condition
        cond_temp = self.gen_expr(node.children[1])
        self.emit('JPF', cond_temp, label_end, '')

        # 3. Body
        self.generate(node.children[3])

        # 4. Update
        self.generate(node.children[2])
        self.emit('JMP', label_start, '', '')

        self.emit_label(label_end)

    def gen_print(self, node):
        # print(expr)
        val_temp = self.gen_expr(node.children[0])
        self.emit('PRINT', val_temp, '', '')

    def gen_input(self, node):
        # input(id)
        var_name = node.leaf
        self.emit('READ', '', '', var_name)

    # --- Expressions ---
    def gen_expr(self, node):
        """
        Evaluates an expression and returns the name of the temporary (or variable)
        holding the result.
        """
        if node.type == 'literal':
            # Ideally load literal into temp, or just return literal string if backend supports immediate
            return str(node.leaf)
        
        elif node.type == 'id':
            return node.leaf
        
        elif node.type == 'array_access':
            # t = arr[idx]
            arr_name = node.leaf
            idx_temp = self.gen_expr(node.children[0])
            res_temp = self.new_temp()
            self.emit('ALOAD', arr_name, idx_temp, res_temp)
            return res_temp

        elif node.type == 'bin_op':
            t1 = self.gen_expr(node.children[0])
            t2 = self.gen_expr(node.children[1])
            res = self.new_temp()
            
            op_map = {
                '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
                '<': 'LT', '>': 'GT', '<=': 'LE', '>=': 'GE',
                '==': 'EQ', '!=': 'NE', '&&': 'AND', '||': 'OR'
            }
            op_code = op_map.get(node.leaf, 'UNKNOWN')
            
            self.emit(op_code, t1, t2, res)
            return res

        elif node.type == 'unary_op':
            t1 = self.gen_expr(node.children[0])
            res = self.new_temp()
            if node.leaf == '-':
                self.emit('NEG', t1, '', res)
            elif node.leaf == '!':
                self.emit('NOT', t1, '', res)
            return res

        elif node.type == 'call':
            # Function call: func(args...)
            # 1. Evaluate args
            args_node = node.children[0]
            arg_temps = []
            if args_node:
                for arg in args_node.children:
                    arg_temps.append(self.gen_expr(arg))
            
            # 2. Push params
            for t in arg_temps:
                self.emit('PARAM', t, '', '')
            
            # 3. Call
            func_name = node.leaf
            res = self.new_temp()
            self.emit('CALL', func_name, len(arg_temps), res)
            return res

        return ''

    def get_output(self):
        """Returns the final combined code string"""
        output = "; --- DATA SECTION ---\n"
        output += "\n".join(self.data_section)
        output += "\n\n; --- CODE SECTION ---\n"
        output += "\n".join(self.code_section)
        return output