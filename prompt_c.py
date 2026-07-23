import csv
import io
import re
from datetime import datetime


def clean_csv_text(csv_text: str) -> tuple[str, list[str]]:
    """Cleans customer CSV data with explicit validation rules."""
    input_stream = io.StringIO(csv_text.strip())
    reader = csv.DictReader(input_stream, skipinitialspace=True)

    expected_headers = [
        "Name",
        "Email",
        "Age",
        "Signup Date",
        "Purchase Amount",
    ]
    if not reader.fieldnames:
        return "", ["Error: CSV is empty or invalid."]

    header_map = {h.strip(): h for h in reader.fieldnames}
    for expected in expected_headers:
        if expected not in header_map:
            return "", [f"Error: Missing required column '{expected}'."]

    cleaned_rows = []
    errors = []
    seen_emails = set()
    email_regex = r"^[\w\.-]+(:\+[\w\.-]+)?@[\w\.-]+\.\w{2,}$"
    date_formats = ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y")

    for row_idx, row in enumerate(reader, start=1):
        raw_name = (row.get(header_map["Name"]) or "").strip()
        raw_email = (row.get(header_map["Email"]) or "").strip()
        raw_age = (row.get(header_map["Age"]) or "").strip()
        raw_date = (row.get(header_map["Signup Date"]) or "").strip()
        raw_amount = (row.get(header_map["Purchase Amount"]) or "").strip()

        try:
            if not raw_name:
                raise ValueError("Missing or empty Name")
            name = raw_name

            if not raw_email:
                raise ValueError("Missing or empty Email")
            email_lower = raw_email.lower()
            if not re.match(email_regex, email_lower):
                raise ValueError(f"Invalid email format: '{raw_email}'")
            if email_lower in seen_emails:
                raise ValueError(
                    f"Duplicate email omitted: '{raw_email}' (already registered)"
                )

            if not raw_age:
                raise ValueError("Missing or empty Age")
            try:
                age_float = float(raw_age)
                age = int(age_float)
            except (ValueError, TypeError):
                raise ValueError(f"Non-numeric Age value: '{raw_age}'")
            if age < 0:
                raise ValueError(f"Negative Age value: '{raw_age}'")
            if age > 120:
                raise ValueError(f"Implausible Age value: '{raw_age}'")

            if not raw_date:
                raise ValueError("Missing or empty Signup Date")
            parsed_date = None
            normalized_date = " ".join(raw_date.split())
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(normalized_date, fmt).date()
                    break
                except ValueError:
                    continue
            if not parsed_date:
                raise ValueError(f"Invalid date format: '{raw_date}'")

            if not raw_amount:
                raise ValueError("Missing or empty Purchase Amount")
            clean_amount = raw_amount.replace("$", "").replace(",", "").strip()
            try:
                amount = round(float(clean_amount), 2)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Non-numeric Purchase Amount: '{raw_amount}'"
                )
            if amount < 0:
                raise ValueError(
                    f"Negative Purchase Amount value: '{raw_amount}'"
                )

            seen_emails.add(email_lower)
            cleaned_rows.append(
                {
                    "Name": name,
                    "Email": email_lower,
                    "Age": age,
                    "Signup Date": parsed_date.isoformat(),
                    "Purchase Amount": f"{amount:.2f}",
                }
            )
        except ValueError as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    output_stream = io.StringIO()
    writer = csv.DictWriter(output_stream, fieldnames=expected_headers)
    writer.writeheader()
    writer.writerows(cleaned_rows)
    return output_stream.getvalue().strip(), errors


# --- Execution Logic ---
if __name__ == "__main__":
    input_filename = "messy_customers.csv"
    output_filename = "cleaned_customers.csv"

    print(f"Reading data from {input_filename}...")

    # Open and read the raw CSV file into a string
    with open(input_filename, mode="r", encoding="utf-8") as file:
        raw_csv_content = file.read()

    # Process the text using the cleaning function
    cleaned_csv_output, validation_errors = clean_csv_text(raw_csv_content)

    # Save the pristine records to a new file
    with open(output_filename, mode="w", encoding="utf-8") as file:
        file.write(cleaned_csv_output)

    print(f"\nProcessing Complete! Cleaned file saved as: {output_filename}")

    # Output compilation results to the console
    print(f"\n--- Validation Error Report ({len(validation_errors)} rejected rows) ---")
    for error in validation_errors:
        print(error)