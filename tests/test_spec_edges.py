"""Targeted checks for rules that are easy to get subtly wrong."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src" / "main.py"


def interpret(source):
    process = subprocess.run(
        [sys.executable, str(MAIN)], input=source, text=True,
        capture_output=True, check=True, encoding="utf-8"
    )
    return process.stdout


class SpecEdgeTests(unittest.TestCase):
    def test_lexing_quote_and_dotted_data(self):
        source = '; ignored\n"a; b\\n\\\"q\\\""\n\'(1 . 2)\n'
        self.assertEqual(interpret(source), '"a; b\\n\\\"q\\\""\n(1 . 2)\n')

    def test_short_circuit_and_truth(self):
        self.assertEqual(
            interpret('(and #f (/ 1 0))\n(or 0 (/ 1 0))\n(if \'() 7 8)\n'),
            '#f\n0\n7\n',
        )

    def test_lexical_scope_and_parallel_let(self):
        source = (
            '(define x 10)\n'
            '(define f (let ((x 4)) (lambda (y) (+ x y))))\n'
            '(f 3)\n'
            '(let ((x 2) (y x)) y)\n'
        )
        self.assertEqual(interpret(source), 'x\nf\n7\n10\n')

    def test_predicate_type_and_identity(self):
        source = (
            '(equal? #t 1)\n'
            '(equal? \'a "a")\n'
            '(eq? \'(1) \'(1))\n'
            '(equal? \'(1) (list 1))\n'
            '(procedure? (lambda (x) x))\n'
        )
        self.assertEqual(interpret(source), '#f\n#f\n#f\n#t\n#t\n')

    def test_equal_nested_proper_and_dotted_values(self):
        source = (
            '(equal? 1 1.0)\n'
            '(equal? #t 1)\n'
            '(equal? \'a "a")\n'
            '(equal? \'(1 (2 3)) (list 1 (list 2 3)))\n'
            '(equal? \'(1 (2 . 3)) (list 1 (cons 2 3)))\n'
            '(equal? \'(1 . 2) (cons 1 2))\n'
            '(equal? \'(1 . 2) \'(1 2))\n'
            '(equal? \'(1 (2 . 3)) \'(1 (2 . 4)))\n'
        )
        self.assertEqual(interpret(source), '#t\n#f\n#f\n#t\n#t\n#t\n#f\n#f\n')

    def test_equal_long_lists_without_python_recursion(self):
        # A flat 1,200-item list exceeds Python's usual recursion limit.
        items = ' '.join(['1'] * 1200)
        different = ' '.join(['1'] * 1199 + ['2'])
        source = (
            f"(equal? '({items}) '({items}))\n"
            f"(equal? '({items}) '({different}))\n"
        )
        self.assertEqual(interpret(source), '#t\n#f\n')

    def test_negative_integer_quotient(self):
        self.assertEqual(interpret('(/ -7 2)\n(quotient -7 2)\n(/ 2)\n'), '-3\n-3\n0.5\n')

    def test_multiple_files_share_global_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.scm"
            second = Path(directory) / "second.scm"
            first.write_text('(define answer 40)\n', encoding="utf-8")
            second.write_text('(+ answer 2)\n', encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(MAIN), str(first), str(second)],
                text=True, capture_output=True, check=True, encoding="utf-8",
            )
        self.assertEqual(process.stdout, 'answer\n42\n')

    def test_nested_quoted_dotted_lists(self):
        self.assertEqual(
            interpret("'(a (b . c))\n'(1 . (2 . ()))\n"),
            '(a (b . c))\n(1 2)\n',
        )

    def test_chained_comparison_and_division(self):
        self.assertEqual(
            interpret("(< 1 2 3)\n(< 'a 'b 'c)\n(/ 9 2 2)\n"),
            '#t\n#t\n2\n',
        )


if __name__ == "__main__":
    unittest.main()
