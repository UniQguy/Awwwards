#!/usr/bin/env python3
"""
ELECTROCART Read-Only Database Viewer CLI (WP1.3).
Provides safe, read-only inspection of the SQLite database for non-developers and faculty:
- List all tables: python scripts/db_viewer.py --tables
- View top N rows: python scripts/db_viewer.py --table <table_name> [--limit N]
- Execute read-only SELECT queries: python scripts/db_viewer.py --query "SELECT * FROM catalog_category"
Strictly blocks all mutation queries (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, REPLACE).
"""

import argparse
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.db import connection

MUTATION_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


def list_tables():
    print("=" * 60)
    print("ELECTROCART DATABASE TABLES (READ-ONLY)")
    print("=" * 60)
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        rows = cursor.fetchall()
        for idx, (name,) in enumerate(rows, 1):
            cursor.execute(f'SELECT COUNT(*) FROM "{name}";')
            count = cursor.fetchone()[0]
            print(f"  {idx:2d}. {name:<40} ({count:,} rows)")
    print("=" * 60)


def show_table(table_name: str, limit: int = 10):
    # Validate table name against sqlite_master to prevent SQL injection
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s;", [table_name])
        if not cursor.fetchone():
            print(f"Error: Table '{table_name}' does not exist.")
            sys.exit(1)

        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT {limit};')
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    print("=" * 80)
    print(f"TABLE: {table_name} (Showing first {len(rows)} rows, limit {limit})")
    print("=" * 80)

    if not rows:
        print("  (Table is currently empty)")
        return

    # Print columns
    header = " | ".join(cols)
    print(header[:140] + ("..." if len(header) > 140 else ""))
    print("-" * 80)
    for r in rows:
        row_str = " | ".join(str(val) if val is not None else "NULL" for val in r)
        print(row_str[:140] + ("..." if len(row_str) > 140 else ""))
    print("=" * 80)


def run_query(query: str):
    cleaned = query.strip()
    if not cleaned.lower().startswith("select") and not cleaned.lower().startswith("explain"):
        print("SECURITY REJECTION: Only read-only SELECT statements are permitted.")
        sys.exit(1)

    if MUTATION_PATTERN.search(cleaned):
        print("SECURITY REJECTION: Mutation keywords detected. Only read-only queries are permitted.")
        sys.exit(1)

    print("=" * 80)
    print(f"QUERY: {cleaned}")
    print("=" * 80)

    with connection.cursor() as cursor:
        try:
            cursor.execute(cleaned)
            cols = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Execution Error: {e}")
            sys.exit(1)

    if not cols:
        print("Query returned no tabular result.")
        return

    print(" | ".join(cols))
    print("-" * 80)
    for r in rows:
        print(" | ".join(str(val) if val is not None else "NULL" for val in r))
    print("-" * 80)
    print(f"Returned {len(rows)} row(s).")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Read-only SQLite database inspection tool for ELECTROCART.")
    parser.add_argument("--tables", action="store_true", help="List all tables in the database with row counts.")
    parser.add_argument("--table", type=str, help="Show the first N rows of a specific table.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of rows to display (default: 10).")
    parser.add_argument("--query", type=str, help="Execute a read-only SELECT statement.")

    args = parser.parse_args()

    if args.tables:
        list_tables()
    elif args.table:
        show_table(args.table, limit=args.limit)
    elif args.query:
        run_query(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
