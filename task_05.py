"""
Task 05 | Expression Validator and Evaluator
Stacks, parsing, exception handling

Problem: Create a calculator for integer expressions containing +, -, *, /,
parentheses, and whitespace. Apply standard operator precedence and parentheses.

Requirements:
  - Do not use eval(), exec(), or third-party parsers.
  - Handle unary minus, malformed expressions, and division by zero.

Sample / Expected Behavior:
  Input: "-(3 + 2) * 4 + 18 / 3" -> -14.0.
"""


class ExpressionError(ValueError):
    """Raised when the expression is syntactically invalid."""


def _tokenize(text):
    """Split the source into ('num', int) and ('op', char) tokens."""
    tokens = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char.isdigit():
            start = index
            while index < length and text[index].isdigit():
                index += 1
            tokens.append(("num", int(text[start:index])))
            continue
        if char in "+-*/()":
            tokens.append(("op", char))
            index += 1
            continue
        raise ExpressionError(
            f"unexpected character {char!r} at position {index}")
    return tokens


class _Parser:
    """Recursive-descent parser: expr -> term -> factor."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def _peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def _advance(self):
        token = self._peek()
        self.position += 1
        return token

    def _accept_operator(self, operators):
        token = self._peek()
        if token is not None and token[0] == "op" and token[1] in operators:
            self.position += 1
            return token[1]
        return None

    def parse(self):
        if not self.tokens:
            raise ExpressionError("expression is empty")
        value = self._expression()
        leftover = self._peek()
        if leftover is not None:
            raise ExpressionError(f"unexpected token {leftover[1]!r}")
        return value

    def _expression(self):
        value = self._term()
        while True:
            operator = self._accept_operator("+-")
            if operator is None:
                return value
            right = self._term()
            value = value + right if operator == "+" else value - right

    def _term(self):
        value = self._factor()
        while True:
            operator = self._accept_operator("*/")
            if operator is None:
                return value
            right = self._factor()
            if operator == "*":
                value = value * right
            else:
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                value = value / right

    def _factor(self):
        token = self._peek()
        if token is None:
            raise ExpressionError("unexpected end of expression")

        kind, symbol = token
        if kind == "num":
            self._advance()
            return symbol

        if symbol == "(":
            self._advance()
            value = self._expression()
            closing = self._peek()
            if closing is None or closing != ("op", ")"):
                raise ExpressionError("missing closing parenthesis")
            self._advance()
            return value

        if symbol in "+-":
            self._advance()
            value = self._factor()          # unary plus / minus
            return -value if symbol == "-" else value

        raise ExpressionError(f"unexpected token {symbol!r}")


def evaluate(expression):
    """Evaluate an integer arithmetic expression and return the result.

    Integers stay ints until a division occurs (standard Python semantics),
    so "1 + 2" -> 3 while "-(3 + 2) * 4 + 18 / 3" -> -14.0.

    Raises ExpressionError for malformed input and ZeroDivisionError when
    a divisor evaluates to zero.
    """
    if not isinstance(expression, str):
        raise TypeError(f"expression must be a str, "
                        f"got {type(expression).__name__}")
    tokens = _tokenize(expression)
    return _Parser(tokens).parse()


SAMPLE_EXPRESSION = "-(3 + 2) * 4 + 18 / 3"


if __name__ == "__main__":
    assert evaluate(SAMPLE_EXPRESSION) == -14.0
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("-5") == -5
    assert evaluate("--5") == 5
    assert evaluate("10 / 4") == 2.5
    assert evaluate("   7   ") == 7

    for bad in ("", "2 +", "(1 + 2", "1 $ 2", "1 / 0", "* 4", "1 2"):
        try:
            evaluate(bad)
        except (ExpressionError, ZeroDivisionError):
            pass
        else:
            raise AssertionError(f"{bad!r} should have raised")
    print("all sample cases passed")
