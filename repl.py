import sys
from pathlib import Path
from lark import Lark, LarkError, UnexpectedCharacters, UnexpectedToken

GRAMMAR_PATH = Path(__file__).parent / "rlite.lark"


def load_parser(parser_type="earley"):
    # Load grammar from file
    with open(GRAMMAR_PATH, "r", encoding="utf-8") as f:
        return Lark(f, start="program", parser=parser_type)


def run_repl():
    parser = load_parser()
    print("RLite Syntax Validator REPL")
    print("Commands: :q to quit, :tree to toggle AST, empty line to submit.\n")

    show_tree = False

    while True:
        try:
            lines = []
            prompt = "rlite> "
            while True:
                line = input(prompt)
                if not line and lines:
                    break
                if line.strip() in (":q", ":exit"):
                    return
                if line.strip() == ":tree":
                    show_tree = not show_tree
                    print(f"AST display: {show_tree}")
                    lines = []
                    break
                lines.append(line)
                prompt = "....> "

            code_input = "\n".join(lines).strip()
            if not code_input:
                continue

            try:
                tree = parser.parse(code_input)
                print("[OK] Valid syntax")
                if show_tree:
                    print(tree.pretty())
            except (UnexpectedToken, UnexpectedCharacters) as err:
                print(f"[ERROR] Syntax error:\n{err}")
            except LarkError as err:
                print(f"[ERROR] Parser error: {err}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    run_repl()