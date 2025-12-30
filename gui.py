import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import io

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer.lexer import lexer
    from Parser.parser import parser
    from Semantic.semantic import semantic_analysis, get_semantic_analysis_report
    from CodeGen.codegeneration import CodeGenerator
except ImportError as e:
    messagebox.showerror("Import Error", f"Critical Import Error: {e}")
    sys.exit(1)

class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AquaLang Compiler")
        self.root.geometry("900x700")

        # --- Top Frame: Input ---
        input_frame = tk.Frame(root, pady=10)
        input_frame.pack(fill=tk.X, padx=10)

        tk.Label(input_frame, text="Source File:").pack(side=tk.LEFT)
        
        self.file_entry = tk.Entry(input_frame, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)
        
        btn_browse = tk.Button(input_frame, text="Browse", command=self.browse_file)
        btn_browse.pack(side=tk.LEFT)

        btn_run = tk.Button(input_frame, text="▶ Run Compiler", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.run_compiler)
        btn_run.pack(side=tk.LEFT, padx=20)

        # --- Bottom Frame: Tabs ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        # Create Tabs
        self.tab_lexer = self.create_tab("Lexer")
        self.tab_parser = self.create_tab("Parser (AST)")
        self.tab_semantic = self.create_tab("Semantic Analysis")
        self.tab_codegen = self.create_tab("Code Generation")

    def create_tab(self, title):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        
        # Scrolled Text Area
        text_area = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 10))
        text_area.pack(expand=True, fill=tk.BOTH)
        
        # Scrollbars
        y_scroll = tk.Scrollbar(frame, command=text_area.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.config(yscrollcommand=y_scroll.set)
        
        return text_area

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def write_log(self, tab, message, color="black"):
        """Helper to write text to a specific tab"""
        tab.config(state=tk.NORMAL)
        # Configure tags for colors if not exists
        tab.tag_config("red", foreground="red")
        tab.tag_config("green", foreground="green")
        tab.tag_config("blue", foreground="blue")
        tab.tag_config("black", foreground="black")

        tag = color if color in ["red", "green", "blue"] else "black"
        tab.insert(tk.END, message + "\n", tag)
        tab.config(state=tk.DISABLED)
        tab.see(tk.END)

    def clear_tabs(self):
        for tab in [self.tab_lexer, self.tab_parser, self.tab_semantic, self.tab_codegen]:
            tab.config(state=tk.NORMAL)
            tab.delete(1.0, tk.END)
            tab.config(state=tk.DISABLED)

    def run_compiler(self):
        filename = self.file_entry.get()
        if not filename:
            messagebox.showwarning("Warning", "Please select a source file first.")
            return

        if not os.path.exists(filename):
            messagebox.showerror("Error", f"File '{filename}' not found.")
            return

        try:
            with open(filename, 'r') as f:
                source_code = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            return

        self.clear_tabs()

        # Flags
        stage_lexer_ok = False
        stage_parser_ok = False
        stage_semantic_ok = False
        ast = None

        # ==================== STEP 1: LEXER ====================
        self.write_log(self.tab_lexer, "--- Lexical Analysis ---", "blue")
        
        lexer.input(source_code)
        lexer.lineno = 1
        lexical_errors = []
        tokens_list = []

        while True:
            tok = lexer.token()
            if not tok:
                break
            if tok.type == 'INVALID':
                lexical_errors.append(f"Line {tok.lineno}: Illegal character '{tok.value}'")
            else:
                tokens_list.append(f"Line {tok.lineno}: {tok.type}({tok.value})")

        if lexical_errors:
            for err in lexical_errors:
                self.write_log(self.tab_lexer, f"❌ {err}", "red")
            self.write_log(self.tab_lexer, "\nResult: FAILED", "red")
        else:
            for t in tokens_list:
                self.write_log(self.tab_lexer, t)
            self.write_log(self.tab_lexer, "\n✅ Result: PASSED", "green")
            stage_lexer_ok = True

        # ==================== STEP 2: PARSER ====================
        if not stage_lexer_ok:
            self.write_log(self.tab_parser, "❌ Skipped due to Lexer errors.", "red")
        else:
            self.write_log(self.tab_parser, "--- Syntax Analysis ---", "blue")
            lexer.lineno = 1
            
            # Capture parser output (print statements) to redirect to GUI
            # Because yacc prints errors to stdout/stderr
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout

            try:
                ast = parser.parse(source_code, lexer=lexer)
                output = new_stdout.getvalue()
                if output:
                    self.write_log(self.tab_parser, output, "red") # Usually errors printed by p_error
            except Exception as e:
                self.write_log(self.tab_parser, f"CRITICAL PARSER CRASH: {e}", "red")
            finally:
                sys.stdout = old_stdout

            if ast:
                self.write_log(self.tab_parser, "✅ AST Generated Successfully!", "green")
                # Basic representation of AST nodes
                self.write_log(self.tab_parser, f"Root Node: {ast.type}", "black")
                if hasattr(ast, 'children'):
                     self.write_log(self.tab_parser, f"Top-level children: {len(ast.children)}", "black")
                
                stage_parser_ok = True
            else:
                self.write_log(self.tab_parser, "❌ Parsing Failed (See errors above).", "red")

        # ==================== STEP 3: SEMANTIC ====================
        if not stage_lexer_ok:
             self.write_log(self.tab_semantic, "❌ Skipped due to Lexer errors.", "red")
        elif not stage_parser_ok:
             self.write_log(self.tab_semantic, "❌ Skipped due to Parser errors.", "red")
        else:
            self.write_log(self.tab_semantic, "--- Semantic Analysis ---", "blue")
            
            # Capture stdout just in case semantic prints something directly
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            
            is_valid = semantic_analysis(ast)
            
            sys.stdout = old_stdout
            
            # Get the structured report
            report = get_semantic_analysis_report()
            
            # Print report to GUI
            self.write_log(self.tab_semantic, report)

            if is_valid:
                self.write_log(self.tab_semantic, "\n✅ Result: PASSED", "green")
                stage_semantic_ok = True
            else:
                self.write_log(self.tab_semantic, "\n❌ Result: FAILED", "red")

        # ==================== STEP 4: CODE GEN ====================
        if not stage_semantic_ok:
            self.write_log(self.tab_codegen, "❌ Skipped due to previous errors.", "red")
        else:
            self.write_log(self.tab_codegen, "--- Intermediate Code Generation ---", "blue")
            try:
                codegen = CodeGenerator(ast)
                tac_output = codegen.get_output()
                self.write_log(self.tab_codegen, tac_output)
                self.write_log(self.tab_codegen, "\n✅ Generated Successfully", "green")
            except Exception as e:
                self.write_log(self.tab_codegen, f"❌ Code Gen Error: {e}", "red")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()