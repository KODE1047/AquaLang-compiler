# main.py
import sys
import os
import argparse
from Lexer.lexer import lexer
from Parser.parser import parser

def main():
    arg_parser = argparse.ArgumentParser(description='AquaLang Compiler Phase 3')
    arg_parser.add_argument('file', help='Path to AquaLang source file', nargs='?')
    arg_parser.add_argument('--debug', action='store_true', help='Enable parser debug mode')
    args = arg_parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = f.read()
            print(f"📂 Processing File: {args.file}")
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        print("⌨️ Interactive Mode")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        data = "\n".join(lines)

    if not data.strip():
        print("Empty input.")
        return

    # --- Phase 2: Lexical ---
    print("-" * 40)
    print("🔍 Phase 2: Lexical Analysis Scan...")
    lexer.input(data)
    lexical_error = False
    while True:
        tok = lexer.token()
        if not tok: break
        if tok.type in ['INVALID', 'BAD_ID_WITH_DOLLAR']:
            print(f"\n❌ Lexical Error at line {tok.lineno}: '{tok.value.strip()}'")
            lexical_error = True
            break
    
    if lexical_error:
        print("\n⛔ Compilation Halted due to Lexical Errors.")
        print("-" * 40)
        return

    print("✅ Lexical Scan Passed.")

    # --- Phase 3: Syntax ---
    print("-" * 40)
    print("🚀 Phase 3: Syntax Analysis...")
    
    lexer.input(data)
    lexer.lineno = 1
    parser.success = True # Initialize success flag
    
    result = parser.parse(data, lexer=lexer, debug=args.debug)

    if parser.success and result:
        print("\n✅ Syntax Correct!")
    else:
        print("\n⚠️ Syntax Analysis Failed.")
    print("-" * 40)

if __name__ == "__main__":
    main()
