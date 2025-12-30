import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import io
import subprocess
import platform
from collections import Counter

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer.lexer import lexer
    from Parser.parser import parser
    from Semantic.semantic import semantic_analysis, symbol_table, error_list
    from CodeGen.codegeneration import CodeGenerator
except ImportError as e:
    messagebox.showerror("Import Error", f"Critical Import Error: {e}")
    sys.exit(1)

class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AquaLang Compiler Environment")
        self.root.geometry("1100x850") 

        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook.Tab", font=('Arial', 10, 'bold'), padding=[10, 5])

        # --- Top Frame: Input ---
        input_frame = tk.Frame(root, pady=15, bg="#f0f0f0")
        input_frame.pack(fill=tk.X)

        tk.Label(input_frame, text="  Source File:", bg="#f0f0f0", font=("Arial", 11)).pack(side=tk.LEFT)
        
        self.file_entry = tk.Entry(input_frame, width=50, font=("Consolas", 11))
        self.file_entry.pack(side=tk.LEFT, padx=10)
        
        btn_browse = tk.Button(input_frame, text="📂 Browse", command=self.browse_file, font=("Arial", 10))
        btn_browse.pack(side=tk.LEFT)

        btn_run = tk.Button(input_frame, text="▶ RUN COMPILER", bg="#2E7D32", fg="white", 
                            font=("Arial", 11, "bold"), padx=15, command=self.run_compiler)
        btn_run.pack(side=tk.LEFT, padx=30)

        # --- Bottom Frame: Tabs ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Create Tabs
        self.tab_lexer = self.create_tab("Lexer")
        self.tab_parser = self.create_tab("Parser (AST)")
        self.tab_semantic = self.create_tab("Semantic")
        self.tab_codegen = self.create_tab("Code Gen")

    def create_tab(self, title):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        
        # Text Area with specific font for alignment
        text_area = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 11), padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)
        
        # Scrollbars
        y_scroll = tk.Scrollbar(frame, command=text_area.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text_area.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        text_area.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Define Color Tags
        text_area.tag_config("title", foreground="#333333", font=("Consolas", 12, "bold"))
        text_area.tag_config("header", foreground="black", background="#e0e0e0", font=("Consolas", 11, "bold"))
        text_area.tag_config("sep", foreground="#999999")
        
        # Colors
        text_area.tag_config("red", foreground="#D32F2F")
        text_area.tag_config("green", foreground="#388E3C")
        text_area.tag_config("blue", foreground="#1976D2")
        text_area.tag_config("cyan", foreground="#0097A7")
        text_area.tag_config("orange", foreground="#F57C00")
        text_area.tag_config("purple", foreground="#7B1FA2")
        text_area.tag_config("grey", foreground="#616161")
        text_area.tag_config("bold", font=("Consolas", 11, "bold"))

        return text_area

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def open_file(self, filepath):
        """Attempts to open the file ONCE."""
        if not os.path.exists(filepath):
            return
        try:
            if platform.system() == 'Darwin':       subprocess.call(('open', filepath))
            elif platform.system() == 'Windows':    os.startfile(filepath)
            else:                                   subprocess.call(('xdg-open', filepath))
        except Exception as e:
            print(f"Warning: Could not open file automatically: {e}")

    def clear_tabs(self):
        for tab in [self.tab_lexer, self.tab_parser, self.tab_semantic, self.tab_codegen]:
            tab.config(state=tk.NORMAL)
            tab.delete(1.0, tk.END)
            tab.config(state=tk.DISABLED)

    def write_skipped(self, tab, stage_name, reason):
        """Helper to write a standardized 'SKIPPED' error message."""
        tab.config(state=tk.NORMAL)
        tab.insert(tk.END, f"❌ SKIPPED: Cannot perform {stage_name}.\n", "title")
        tab.insert(tk.END, f"   Reason: Previous stage [{reason}] failed.\n", "red")
        tab.config(state=tk.DISABLED)

    # =========================================================================
    #  RENDER HELPERS
    # =========================================================================

    def render_lexer_table(self, token_list, errors):
        tab = self.tab_lexer
        tab.config(state=tk.NORMAL)

        # Dimensions
        w_idx, w_type, w_val, w_line = 6, 20, 35, 6
        
        # Header
        header = f"| {'#':<{w_idx}} | {'TYPE':<{w_type}} | {'VALUE':<{w_val}} | {'LN':<{w_line}} |"
        sep    = f"+{'-'*(w_idx+2)}+{'-'*(w_type+2)}+{'-'*(w_val+2)}+{'-'*(w_line+2)}+"

        tab.insert(tk.END, "LEXICAL ANALYSIS REPORT\n", "title")
        tab.insert(tk.END, sep + "\n", "sep")
        tab.insert(tk.END, header + "\n", "header")
        tab.insert(tk.END, sep + "\n", "sep")

        for i, t in enumerate(token_list, 1):
            val_str = repr(t['value'])
            if len(val_str) > 32: val_str = val_str[:30] + "..."
            
            # Row
            tab.insert(tk.END, "| ", "sep")
            tab.insert(tk.END, f"{str(i):<{w_idx}} ", "grey")
            tab.insert(tk.END, "| ", "sep")
            
            c_type = "red" if t['type'] == 'INVALID' else "blue"
            tab.insert(tk.END, f"{t['type']:<{w_type}} ", c_type)
            tab.insert(tk.END, "| ", "sep")
            
            c_val = "red" if t['type'] == 'INVALID' else "green"
            tab.insert(tk.END, f"{val_str:<{w_val}} ", c_val)
            tab.insert(tk.END, "| ", "sep")
            
            tab.insert(tk.END, f"{str(t['line']):<{w_line}} ", "orange")
            tab.insert(tk.END, "|\n", "sep")

        tab.insert(tk.END, sep + "\n", "sep")
        
        if errors:
            tab.insert(tk.END, "\n❌ ERRORS FOUND:\n", "red")
            for e in errors: tab.insert(tk.END, f"  • {e}\n", "red")
        else:
            tab.insert(tk.END, "\n✅ LEXER PASSED", "green")
        
        tab.config(state=tk.DISABLED)

    def render_ast_tree(self, node, prefix="", is_last=True):
        tab = self.tab_parser
        connector = "└── " if is_last else "├── "
        
        tab.insert(tk.END, prefix + connector, "grey")
        
        if hasattr(node, 'type'):
            node_text = f"[{node.type.upper()}] "
            tab.insert(tk.END, node_text, "purple")
            
            if hasattr(node, 'leaf') and node.leaf:
                 tab.insert(tk.END, f"{node.leaf}", "green")
            
            tab.insert(tk.END, "\n")
            
            if hasattr(node, 'children') and node.children:
                children = [c for c in node.children if c]
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    self.render_ast_tree(child, new_prefix, is_last_child)
        else:
            tab.insert(tk.END, f"{str(node)}\n", "cyan")

    def render_semantic_table(self):
        tab = self.tab_semantic
        tab.config(state=tk.NORMAL)

        # 1. Errors
        if error_list:
            tab.insert(tk.END, "❌ SEMANTIC ERRORS FOUND:\n", "title")
            for err in error_list:
                tab.insert(tk.END, f"  • {err}\n", "red")
            tab.insert(tk.END, "\n")
        else:
            tab.insert(tk.END, "✅ NO SEMANTIC ERRORS\n\n", "green")

        # 2. Symbol Table
        if symbol_table.scopes:
            tab.insert(tk.END, "GLOBAL SYMBOL TABLE\n", "title")
            
            w_id, w_type, w_cat = 25, 15, 15
            sep = f"+{'-'*(w_id+2)}+{'-'*(w_type+2)}+{'-'*(w_cat+2)}+"
            header = f"| {'IDENTIFIER':<{w_id}} | {'TYPE':<{w_type}} | {'CATEGORY':<{w_cat}} |"
            
            tab.insert(tk.END, sep + "\n", "sep")
            tab.insert(tk.END, header + "\n", "header")
            tab.insert(tk.END, sep + "\n", "sep")
            
            global_scope = symbol_table.scopes[0]
            for name, info in global_scope.items():
                tab.insert(tk.END, "| ", "sep")
                tab.insert(tk.END, f"{name:<{w_id}} ", "bold")
                tab.insert(tk.END, "| ", "sep")
                
                t_color = "blue"
                if info['type'] in ['int', 'float']: t_color = "cyan"
                if info['type'] == 'bool': t_color = "orange"
                
                tab.insert(tk.END, f"{info['type']:<{w_type}} ", t_color)
                tab.insert(tk.END, "| ", "sep")
                tab.insert(tk.END, f"{info['category']:<{w_cat}} ", "purple")
                tab.insert(tk.END, "|\n", "sep")
            
            tab.insert(tk.END, sep + "\n", "sep")

        tab.config(state=tk.DISABLED)

    def render_codegen(self, tac_code):
        tab = self.tab_codegen
        tab.config(state=tk.NORMAL)
        
        tab.insert(tk.END, "THREE-ADDRESS CODE (TAC)\n", "title")
        tab.insert(tk.END, "="*40 + "\n", "sep")

        lines = tac_code.split('\n')
        for line in lines:
            if not line.strip(): 
                tab.insert(tk.END, "\n")
                continue
            
            if line.startswith(';'):
                tab.insert(tk.END, line + "\n", "grey")
            elif line.strip().endswith(':'):
                tab.insert(tk.END, line + "\n", "orange")
            elif line.startswith('\t'):
                parts = line.strip().split(maxsplit=1)
                opcode = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                
                tab.insert(tk.END, "    ")
                tab.insert(tk.END, f"{opcode:<8}", "blue")
                
                if args:
                    arg_parts = args.split(',')
                    for i, arg in enumerate(arg_parts):
                        arg = arg.strip()
                        if arg.startswith('t') and arg[1:].isdigit():
                            tab.insert(tk.END, arg, "green")
                        elif arg.startswith('L') and arg[1:].isdigit():
                            tab.insert(tk.END, arg, "orange")
                        elif arg.isdigit():
                            tab.insert(tk.END, arg, "cyan")
                        else:
                            tab.insert(tk.END, arg, "black")
                        
                        if i < len(arg_parts) - 1:
                            tab.insert(tk.END, ", ", "grey")
                tab.insert(tk.END, "\n")
            else:
                tab.insert(tk.END, line + "\n")

        tab.config(state=tk.DISABLED)


    # =========================================================================
    #  MAIN PIPELINE
    # =========================================================================

    def run_compiler(self):
        filename = self.file_entry.get()
        if not filename or not os.path.exists(filename):
            messagebox.showerror("Error", "Please select a valid file.")
            return

        with open(filename, 'r') as f:
            source_code = f.read()

        self.clear_tabs()
        
        # Flags
        s_lexer, s_parser, s_semantic = False, False, False
        ast = None

        # --- 1. Lexer ---
        lexer.input(source_code)
        lexer.lineno = 1
        tokens = []
        lex_errors = []
        
        while True:
            t = lexer.token()
            if not t: break
            tokens.append({'type': t.type, 'value': t.value, 'line': t.lineno})
            if t.type == 'INVALID':
                lex_errors.append(f"Line {t.lineno}: Invalid Token '{t.value}'")
                break
        
        self.render_lexer_table(tokens, lex_errors)
        if not lex_errors: s_lexer = True

        # --- 2. Parser ---
        if s_lexer:
            self.tab_parser.config(state=tk.NORMAL)
            self.tab_parser.insert(tk.END, "ABSTRACT SYNTAX TREE (AST)\n", "title")
            self.tab_parser.insert(tk.END, "="*40 + "\n", "sep")
            
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            
            lexer.lineno = 1
            try:
                ast = parser.parse(source_code, lexer=lexer)
                parse_errs = new_stdout.getvalue()
                
                if parse_errs:
                    self.tab_parser.insert(tk.END, "\n❌ PARSE ERRORS:\n", "red")
                    self.tab_parser.insert(tk.END, parse_errs, "red")
                
                if ast:
                    self.render_ast_tree(ast)
                    s_parser = True
                    
                    # Generate Image
                    try:
                        img_name = "ast_output"
                        # Only try to draw if not already drawing
                        ast.draw_tree(output_file=img_name)
                        full_path = os.path.abspath(img_name + ".png")
                        
                        self.tab_parser.insert(tk.END, f"\n✅ Graph saved to: {full_path}", "green")
                        # Open ONCE
                        self.open_file(full_path)
                    except Exception as e:
                         self.tab_parser.insert(tk.END, f"\n⚠️ GraphViz Error: {e}", "orange")

                else:
                    self.tab_parser.insert(tk.END, "\n❌ Failed to build AST.", "red")
            except Exception as e:
                self.tab_parser.insert(tk.END, f"\n❌ CRITICAL CRASH: {e}", "red")
            finally:
                sys.stdout = old_stdout
            self.tab_parser.config(state=tk.DISABLED)
        else:
             self.write_skipped(self.tab_parser, "Parser", "Lexer")

        # --- 3. Semantic ---
        if s_parser:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO() 
            is_valid = semantic_analysis(ast)
            sys.stdout = old_stdout
            
            self.render_semantic_table()
            if is_valid: s_semantic = True
        else:
            reason = "Lexer" if not s_lexer else "Parser"
            self.write_skipped(self.tab_semantic, "Semantic Analysis", reason)

        # --- 4. Code Gen ---
        if s_semantic:
            try:
                cg = CodeGenerator(ast)
                self.render_codegen(cg.get_output())
                with open(filename+".tac", "w") as f:
                    f.write(cg.get_output())
            except Exception as e:
                self.tab_codegen.config(state=tk.NORMAL)
                self.tab_codegen.insert(tk.END, f"❌ Code Gen Error: {e}", "red")
                self.tab_codegen.config(state=tk.DISABLED)
        else:
            reason = "Semantic Analysis"
            if not s_parser: reason = "Parser"
            if not s_lexer: reason = "Lexer"
            self.write_skipped(self.tab_codegen, "Code Generation", reason)

if __name__ == "__main__":
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()