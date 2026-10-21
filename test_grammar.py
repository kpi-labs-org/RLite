import unittest
from pathlib import Path
from lark import Lark, LarkError

GRAMMAR_PATH = Path(__file__).parent / "rlite.lark"


class TestRLiteGrammar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GRAMMAR_PATH, "r", encoding="utf-8") as f:
            cls.parser = Lark(f, start="program", parser="earley")

    def assert_valid(self, code: str):
        try:
            tree = self.parser.parse(code)
            self.assertIsNotNone(tree)
        except LarkError as e:
            self.fail(f"Parsing failed unexpectedly: {e}")

    def assert_invalid(self, code: str):
        with self.assertRaises(LarkError):
            self.parser.parse(code)

    def test_single_expression(self):
        self.assert_valid("1 + 1")
        self.assert_valid("2 ^ 3 ^ 2")
        self.assert_valid("!ready & (x < 10)")

    def test_declarations(self):
        code = """
        int x;
        int y <- 10;
        const float PI <- 3.14159;
        type Score <- int;
        Score s <- 100;
        int[] arr <- c(1, 2, 3);
        """
        self.assert_valid(code)

    def test_control_flow(self):
        code = """
        if (x > 0) {
            print("positive");
        } else if (x == 0) {
            print("zero");
        } else {
            print("negative");
        }

        while (i <= 10) {
            i <- i + 1;
        }
        """
        self.assert_valid(code)

    def test_functions(self):
        code = """
        int factorial <- function(int n) {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }
        int res <- factorial(5);
        """
        self.assert_valid(code)

    def test_invalid_syntax(self):
        self.assert_invalid("int x <- 10")  # Missing semicolon
        self.assert_invalid("bool bad <- a < b < c;")  # Chained comparisons
        self.assert_invalid("const int x;")  # Const without initializer
        self.assert_invalid("10 <- x;")  # Literal as lvalue


if __name__ == "__main__":
    unittest.main()