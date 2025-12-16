# /main.py
import sys
import os

# --- Path Configuration ---
# This ensures Python sees 'Lexer' and 'Parser' as packages relative to main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer.lexer import lexer
    from Parser.parser import parser
except ImportError as e:
    print("❌ Import Error: Could not find Lexer or Parser modules.")
    print(f"Details: {e}")
    print("\nEnsure your directory structure looks like this:")
    print("  /Project_Root")
    print("    main.py")
    print("    test.txt")
    print("    /Lexer")
    print("      __init__.py")
    print("      lexer.py")
    print("    /Parser")
    print("      __init__.py")
    print("      parser.py")
    sys.exit(1)

def main():
    # 1. Check Arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename>")
        return

    filename = sys.argv[1]

    # 2. Read File
    try:
        with open(filename, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        return

    print(f"--- Compiling: {filename} ---")

    # 3. Lexer Pass (Visualization Only)
    # We run this separately just to show you the tokens.
    print("\n[Step 1] Lexical Analysis:")
    lexer.input(source_code)
    
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(f"  {tok.type:<15} {tok.value}")
    
    # --- CRITICAL: Reset Lexer ---
    # Since we consumed tokens above, we must reset the lexer line number
    # and re-feed the input so the Parser sees them from the start.
    lexer.lineno = 1

    # 4. Parser Pass
    print("\n[Step 2] Syntax Analysis (AST Generation):")
    
    # We pass the raw source code. The parser calls lexer.input() internally
    # or uses the lexer instance we pass to it.
    result = parser.parse(source_code, lexer=lexer)

    # 5. Output Result
    if result:
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        print("\n✅ AST Generated Successfully:\n")
        pp.pprint(result)
    else:
        print("\n❌ Parsing Failed (See errors above).")

if __name__ == "__main__":
    main()