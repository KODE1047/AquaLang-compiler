import customtkinter as ctk
import sys
import threading

# --- Import Parser ---
try:
    from Parser.parser import parser
except ImportError as e:
    print(f"Error importing parser: {e}")
    parser = None

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- Helper: AST Pretty Printer ---
def format_ast(node, level=0):
    """
    Recursively formats the AST Node into a readable string tree.
    Assumes Node has attributes: type, children (list), leaf (value).
    """
    if not node:
        return ""
    
    # Indentation for tree structure
    indent = "  " * level
    branch = "└── " if level > 0 else ""
    
    # Get Node details (safely)
    node_type = getattr(node, 'type', 'Unknown')
    leaf_val = getattr(node, 'leaf', None)
    children = getattr(node, 'children', [])

    # Format the current line
    if leaf_val is not None:
        result = f"{indent}{branch}[{node_type}] : {leaf_val}\n"
    else:
        result = f"{indent}{branch}[{node_type}]\n"

    # Recursively format children
    if children:
        # If children is a list, iterate; otherwise treat as single node
        if isinstance(children, list):
            for child in children:
                result += format_ast(child, level + 1)
        else:
            result += format_ast(children, level + 1)
            
    return result

# --- Helper: Stdout Redirector ---
class ConsoleRedirector:
    """Redirects sys.stdout to the GUI console widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        # Schedule the update on the main thread to avoid crashing
        self.text_widget.after(0, self._append_text, string)

    def _append_text(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class CompilerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Compiler Workbench")
        self.geometry("1200x800")
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1) # Main content area expands
        self.grid_rowconfigure(0, weight=1)    # Full height

        # --- Sidebar (Left) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="COMPILER V1", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_load = ctk.CTkButton(self.sidebar, text="📂 Load Source", command=self.load_file)
        self.btn_load.grid(row=1, column=0, padx=20, pady=10)

        self.btn_compile = ctk.CTkButton(self.sidebar, text="▶ BUILD AST", 
                                       fg_color="#00A86B", hover_color="#008554", # Success Green
                                       height=40, font=ctk.CTkFont(weight="bold"),
                                       command=self.run_compiler)
        self.btn_compile.grid(row=2, column=0, padx=20, pady=20)

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Ready", text_color="gray")
        self.lbl_status.grid(row=9, column=0, padx=20, pady=20, sticky="s")

        # --- Main Content (Right) ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_area.grid_columnconfigure(0, weight=1) # Editor
        self.main_area.grid_columnconfigure(1, weight=1) # AST
        self.main_area.grid_rowconfigure(0, weight=3)    # Editors height
        self.main_area.grid_rowconfigure(1, weight=1)    # Console height

        # 1. Code Editor
        self.lbl_code = ctk.CTkLabel(self.main_area, text="Source Code (Input)", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_code.grid(row=0, column=0, sticky="w", padx=5)
        
        self.editor = ctk.CTkTextbox(self.main_area, font=("Consolas", 14), undo=True)
        self.editor.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0, 10))
        self.editor.insert("0.0", "func main() {\n    int x = 10;\n    if (x > 5) {\n        print(x);\n    }\n}")

        # 2. AST Viewer
        self.lbl_ast = ctk.CTkLabel(self.main_area, text="Abstract Syntax Tree (Structure)", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_ast.grid(row=0, column=1, sticky="w", padx=5)
        
        self.ast_viewer = ctk.CTkTextbox(self.main_area, font=("Consolas", 12), state="disabled", fg_color="#1a1a1a", text_color="#A0A0A0")
        self.ast_viewer.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 10))

        # 3. Console (Bottom)
        self.lbl_console = ctk.CTkLabel(self.main_area, text="System Output & Errors", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_console.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)

        self.console = ctk.CTkTextbox(self.main_area, height=150, font=("Consolas", 12), state="disabled", fg_color="#101010")
        self.console.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 5))

        # Redirect Stdout
        sys.stdout = ConsoleRedirector(self.console)

    def load_file(self):
        path = ctk.filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, 'r') as f:
                self.editor.delete("0.0", "end")
                self.editor.insert("0.0", f.read())
            print(f"[GUI] Loaded file: {path}")

    def run_compiler(self):
        # Clear output windows
        self.ast_viewer.configure(state="normal")
        self.ast_viewer.delete("0.0", "end")
        self.ast_viewer.configure(state="disabled")
        
        self.console.configure(state="normal")
        self.console.delete("0.0", "end")
        self.console.configure(state="disabled")

        code = self.editor.get("0.0", "end")
        
        print("--- Compiling... ---")
        self.lbl_status.configure(text="Compiling...", text_color="yellow")

        # Run parsing
        try:
            if parser:
                # 1. Parse the Code
                result_ast = parser.parse(code)
                
                # 2. Check Result
                if result_ast:
                    print("✔ PARSE SUCCESSFUL.")
                    self.lbl_status.configure(text="Build Success", text_color="#00A86B")
                    
                    # 3. Format AST to String
                    tree_str = format_ast(result_ast)
                    
                    # 4. Display AST
                    self.ast_viewer.configure(state="normal")
                    self.ast_viewer.insert("0.0", tree_str)
                    self.ast_viewer.configure(state="disabled")
                else:
                    print("❌ PARSE FAILED (See errors above).")
                    self.lbl_status.configure(text="Parse Failed", text_color="#FF5555")
            else:
                print("CRITICAL: Parser not loaded.")
        except Exception as e:
            print(f"❌ COMPILER CRASHED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = CompilerGUI()
    app.mainloop()