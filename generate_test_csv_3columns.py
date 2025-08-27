"""
Generate a sample CSV file for testing create_users_from_csv.py
By default generates 'test_users.csv' with 6 sample rows covering roles and projects.

Example:
  python generate_test_csv.py --out test_users.csv
"""

import csv
import argparse

SAMPLE_ROWS = [
    {"Username": "alice", "Password": "Passw0rd!", "Role": "developer", "Project": "demo"},
    {"Username": "bob", "Password": "S3cret!", "Role": "guest", "Project": "demo"},
    {"Username": "carol", "Password": "TopSecret1", "Role": "maintainer", "Project": "demo"},
    {"Username": "dave", "Password": "InitPass9", "Role": "projectAdmin", "Project": "ops"},
    {"Username": "eve", "Password": "EvePass#1", "Role": "developer", "Project": "ops"},
    {"Username": "frank", "Password": "Temp1234", "Role": "guest", "Project": ""},
]

FIELDNAMES = ["Username", "Password", "Role", "Project"]


def generate(out: str, rows: int = None):
    with open(out, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        if rows is None:
            for r in SAMPLE_ROWS:
                writer.writerow(r)
        else:
            # cycle sample rows if rows > len(SAMPLE_ROWS)
            for i in range(rows):
                writer.writerow(SAMPLE_ROWS[i % len(SAMPLE_ROWS)])
    print(f"Wrote sample CSV to {out}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate sample CSV for Harbor user creation')
    parser.add_argument('--out', required=False, default='test_users.csv', help='Output CSV file')
    parser.add_argument('--rows', required=False, type=int, help='Number of rows to generate (will repeat sample set)')
    args = parser.parse_args()
    generate(args.out, args.rows)
