# /main.py
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer.lexer import lexer
    from Parser.parser import parser
    from Semantic.semantic import semantic_analysis, get_semantic_analysis_report
    from CodeGen.codegeneration import CodeGenerator
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename>")
        return

    filename = sys.argv[1]
    
    # 1. READ FILE
    try:
        with open(filename, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        return

    print(f"--- 🚀 Compiling Target: {filename} ---")

    # --- PIPELINE STATE FLAGS ---
    stage_lexer_ok = False
    stage_parser_ok = False
    stage_semantic_ok = False
    ast = None

    # =========================================================================
    # STAGE 1: LEXICAL ANALYSIS (Tokenizing)
    # =========================================================================
    print_separator("[Step 1] Lexical Analysis")
    
    lexer.input(source_code)
    lexical_errors = []

    # Iterate through all tokens to check for errors BEFORE parsing
    while True:
        tok = lexer.token()
        if not tok:
            break
        if tok.type == 'INVALID':
            lexical_errors.append(f"Line {tok.lineno}: Illegal character/sequence '{tok.value}'")
    
    if lexical_errors:
        print("❌ Lexical Errors Found:")
        for err in lexical_errors:
            print(f"   - {err}")
        print("\n❌ Lexer Failed.")
    else:
        print("✅ Lexical Analysis Passed! (All tokens valid)")
        stage_lexer_ok = True

    # =========================================================================
    # STAGE 2: SYNTAX ANALYSIS (Parsing)
    # =========================================================================
    print_separator("[Step 2] Syntax Analysis")

    if not stage_lexer_ok:
        print(f"❌ SKIPPED: Cannot perform Syntax Analysis.")
        print(f"   Reason: Previous stage [Lexer] failed.")
    else:
        # Reset lexer line counter and input for the parser to use freshly
        lexer.lineno = 1
        
        # Run Parser
        # The parser will print specific syntax errors to console via p_error
        ast = parser.parse(source_code, lexer=lexer)

        if ast:
            print("✅ AST Generated Successfully!")
            stage_parser_ok = True
            
            # Optional: Draw Tree
            try:
                ast.draw_tree(output_file="ast_output")
                print("   (Graphviz tree saved to 'ast_output.png')")
            except Exception:
                pass 
        else:
            print("❌ Parsing Failed: valid AST could not be built.")
            print("   (Check the syntax errors reported above ⬆️)")

    # =========================================================================
    # STAGE 3: SEMANTIC ANALYSIS
    # =========================================================================
    print_separator("[Step 3] Semantic Analysis")

    if not stage_lexer_ok:
        print(f"❌ SKIPPED: Cannot perform Semantic Analysis.")
        print(f"   Reason: Previous stage [Lexer] failed.")
    elif not stage_parser_ok:
        print(f"❌ SKIPPED: Cannot perform Semantic Analysis.")
        print(f"   Reason: Previous stage [Parser] failed.")
    else:
        # Run Semantic Check
        is_valid = semantic_analysis(ast)
        
        # Always print the report
        print(get_semantic_analysis_report())

        if is_valid:
            print("\n✅ Semantic Analysis Passed!")
            stage_semantic_ok = True
        else:
            print("\n❌ Semantic Analysis Failed.")

    # =========================================================================
    # STAGE 4: CODE GENERATION
    # =========================================================================
    print_separator("[Step 4] Intermediate Code Generation")

    if not stage_lexer_ok:
        print(f"❌ SKIPPED: Cannot perform Code Generation.")
        print(f"   Reason: Previous stage [Lexer] failed.")
    elif not stage_parser_ok:
        print(f"❌ SKIPPED: Cannot perform Code Generation.")
        print(f"   Reason: Previous stage [Parser] failed.")
    elif not stage_semantic_ok:
        print(f"❌ SKIPPED: Cannot perform Code Generation.")
        print(f"   Reason: Previous stage [Semantic Analysis] failed.")
    else:
        try:
            codegen = CodeGenerator(ast)
            tac_output = codegen.get_output()
            
            # Print to Console
            print("\n--- 3-Address Code Output ---")
            print(tac_output)
            print("-----------------------------")

            # Save to File
            out_file = filename + ".tac"
            with open(out_file, 'w') as f:
                f.write(tac_output)
            print(f"\n✅ Success! TAC saved to: {out_file}")
            
        except Exception as e:
            print(f"❌ Code Generation Crashed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()