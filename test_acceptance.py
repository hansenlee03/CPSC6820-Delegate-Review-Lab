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


class AcceptanceTests(unittest.TestCase):
    def test_accepts_plus_alias_email(self) -> None:
        csv_text = """Name,Email,Age,Signup Date,Purchase Amount
Alex Research,Alex+Research@Example.com,30,2024-01-15,25.50
"""

        cleaned_output, errors = clean_csv_text(csv_text)
        rows = list(csv.DictReader(io.StringIO(cleaned_output)))

        # A valid plus-alias email should be accepted without errors.
        self.assertEqual(errors, [])

        # The valid row should remain in the cleaned CSV output.
        self.assertEqual(len(rows), 1)

        # The email address should be normalized to lowercase without
        # removing the plus alias.
        self.assertEqual(rows[0]["Email"], "alex+research@example.com")

    def test_rejects_decimal_age_without_truncating(self) -> None:
        csv_text = """Name,Email,Age,Signup Date,Purchase Amount
Taylor Morgan,taylor@example.com,25.7,2024-01-15,25.50
"""

        cleaned_output, errors = clean_csv_text(csv_text)
        rows = list(csv.DictReader(io.StringIO(cleaned_output)))

        # A decimal age is invalid and must not be silently truncated.
        self.assertEqual(rows, [])

        # The rejected row should produce at least one validation error.
        self.assertTrue(errors)

        # The error should identify the age problem and explain that a
        # whole-number value is required.
        error_text = " ".join(str(error) for error in errors).lower()
        self.assertIn("age", error_text)
        self.assertIn("whole number", error_text)

    def test_missing_input_file_is_handled_gracefully(self) -> None:
        script_path = PROJECT_ROOT / "prompt_c.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
            )

        combined_output = f"{result.stdout}\n{result.stderr}"

        # The program should report a clear error rather than failing silently.
        self.assertIn("error", combined_output.lower())

        # The message should identify the missing default input file.
        self.assertIn("messy_customers.csv", combined_output)

        # Graceful handling means no unhandled Python traceback is displayed.
        self.assertNotIn("traceback", combined_output.lower())


if __name__ == "__main__":
    unittest.main()
