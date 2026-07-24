import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from prompt_c import clean_csv_text  # noqa: E402


class PromptCRegressionTests(unittest.TestCase):
    def test_accepts_and_lowercases_plus_alias_email(self) -> None:
        csv_text = """Name,Email,Age,Signup Date,Purchase Amount
Casey Alias,Name+Tag@Example.com,30,2024-01-15,25.50
"""

        cleaned_output, errors = clean_csv_text(csv_text)
        rows = list(csv.DictReader(io.StringIO(cleaned_output)))

        self.assertEqual(errors, [])
        self.assertEqual(rows[0]["Email"], "name+tag@example.com")

    def test_rejects_decimal_age_as_not_a_whole_number(self) -> None:
        csv_text = """Name,Email,Age,Signup Date,Purchase Amount
Taylor Morgan,taylor@example.com,25.7,2024-01-15,25.50
"""

        cleaned_output, errors = clean_csv_text(csv_text)
        rows = list(csv.DictReader(io.StringIO(cleaned_output)))

        self.assertEqual(rows, [])
        error_text = " ".join(errors).lower()
        self.assertIn("age", error_text)
        self.assertIn("whole number", error_text)

    def test_accepts_age_boundaries_zero_and_120(self) -> None:
        csv_text = """Name,Email,Age,Signup Date,Purchase Amount
Zero Age,zero@example.com,0,2024-01-15,25.50
Upper Age,upper@example.com,120,2024-01-15,25.50
"""

        cleaned_output, errors = clean_csv_text(csv_text)
        rows = list(csv.DictReader(io.StringIO(cleaned_output)))

        self.assertEqual(errors, [])
        self.assertEqual([row["Age"] for row in rows], ["0", "120"])

    def test_missing_default_input_file_exits_cleanly(self) -> None:
        result = self.run_script_without_default_input()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("messy_customers.csv", result.stderr)
        self.assertNotIn("traceback", result.stderr.lower())

    def test_unreadable_default_input_file_exits_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir, "messy_customers.csv")
            input_path.write_text("Name,Email,Age,Signup Date,Purchase Amount\n")
            original_mode = input_path.stat().st_mode
            input_path.chmod(0)
            try:
                result = subprocess.run(
                    [sys.executable, str(PROJECT_ROOT / "prompt_c.py")],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            finally:
                input_path.chmod(original_mode)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("messy_customers.csv", result.stderr)
        self.assertNotIn("traceback", result.stderr.lower())

    def run_script_without_default_input(self) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            return subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "prompt_c.py")],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
            )


if __name__ == "__main__":
    unittest.main()
