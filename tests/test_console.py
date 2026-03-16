from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest
from unittest import mock

from brave_updater.console import make_logger, prompt_yes_no


class ConsoleTests(unittest.TestCase):
    def test_make_logger_writes_to_stdout_by_default(self) -> None:
        output = StringIO()
        logger = make_logger()

        with redirect_stdout(output):
            logger("hello")

        self.assertEqual(output.getvalue().strip(), "hello")

    def test_make_logger_writes_to_stderr_in_print_only_mode(self) -> None:
        output = StringIO()
        logger = make_logger(print_only_mode=True)

        with redirect_stderr(output):
            logger("hello")

        self.assertEqual(output.getvalue().strip(), "hello")

    def test_prompt_yes_no_uses_default_for_non_interactive_stdin(self) -> None:
        fake_stdin = mock.Mock()
        fake_stdin.isatty.return_value = False

        with mock.patch("sys.stdin", fake_stdin):
            self.assertFalse(prompt_yes_no("Continue?", default_no=True))
            self.assertTrue(prompt_yes_no("Continue?", default_no=False))

    def test_prompt_yes_no_accepts_yes_in_interactive_mode(self) -> None:
        fake_stdin = mock.Mock()
        fake_stdin.isatty.return_value = True

        with mock.patch("sys.stdin", fake_stdin):
            with mock.patch("builtins.input", return_value="yes"):
                self.assertTrue(prompt_yes_no("Continue?", default_no=True))

    def test_prompt_yes_no_rejects_no_in_interactive_mode(self) -> None:
        fake_stdin = mock.Mock()
        fake_stdin.isatty.return_value = True

        with mock.patch("sys.stdin", fake_stdin):
            with mock.patch("builtins.input", return_value="n"):
                self.assertFalse(prompt_yes_no("Continue?", default_no=False))


if __name__ == "__main__":
    unittest.main()
