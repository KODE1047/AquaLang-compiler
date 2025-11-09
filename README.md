# <*University Project*> AquaLang-compiler
This project is an implementation of a compiler for AquaLang, an educational language combining C and Python concepts.

## Tech Stack

* **Python** 
* **PLY (Python Lex-Yacc)** 

## Project Requirements

As defined by the project specifications, this lexer:

* Uses an automated tool (PLY) to generate the scanner .
* Implements the complete set of regular expressions for all AquaLang lexical structures (keywords, identifiers, operators, etc.) .
* Correctly identifies and tokenizes all valid language tokens .
* Handles and filters comments (both single-line `//` and multi-line `/* ... */`) and whitespace .
* Detects and reports lexical errors, such as invalid characters .

## Installation

1.  Clone the repository:
    ```sh
    git clone [https://github.com/KODE1047/AquaLang-compiler.git](https://github.com/KODE1047/AquaLang-compiler.git)
    cd AquaLang-compiler
    ```
2.  Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## License

Distributed under the MIT License. See `LICENSE` for more information.
