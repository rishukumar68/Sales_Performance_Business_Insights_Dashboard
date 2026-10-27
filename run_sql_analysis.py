from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "processed" / "clean_sales.csv"
SQL_PATH = ROOT / "sql" / "analysis_queries.sql"
DB_PATH = ROOT / "data" / "processed" / "sales_analysis.db"

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Missing cleaned data: {CSV_PATH}")

if not SQL_PATH.exists():
    raise FileNotFoundError(f"Missing SQL file: {SQL_PATH}")

# Load the cleaned dataset and normalize dates for SQLite.
df = pd.read_csv(
    CSV_PATH,
    dtype={"InvoiceNo": "string"},
    low_memory=False
)
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
).dt.strftime("%Y-%m-%d %H:%M:%S")

with sqlite3.connect(DB_PATH) as conn:
    df.to_sql("clean_sales", conn, if_exists="replace", index=False)

    # Each numbered query is separated by its SQL comment heading.
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    sections = {}
    current_title = None
    current_lines = []

    for line in sql_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("-- ") and stripped[3:4].isdigit():
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = stripped[3:]
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()

    for title, query in sections.items():
        query = "\n".join(
            line for line in query.splitlines()
            if not line.strip().startswith("--")
        ).strip()

        if not query:
            continue

        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
        try:
            result = pd.read_sql_query(query, conn)
            print(result.head(10).to_string(index=False))
            print(f"\nRows returned: {len(result)}")
        except Exception as exc:
            print(f"QUERY ERROR: {exc}")

print(f"\nDatabase created at: {DB_PATH}")


print("\nChecking invoice dates for Saturdays...")

saturday_rows = df[
    pd.to_datetime(df["InvoiceDate"], errors="coerce").dt.dayofweek == 5
]

print("Saturday rows in cleaned CSV:", len(saturday_rows))