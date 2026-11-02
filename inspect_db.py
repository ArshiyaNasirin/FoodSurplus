"""
inspect_db.py - CLI SQLite Database Inspector for FoodResQ AI.

Usage:
  python inspect_db.py            # Overview of all tables and record counts
  python inspect_db.py users      # View records in 'users' table
  python inspect_db.py ngos       # View records in 'ngos' table
  python inspect_db.py surplus_food
  python inspect_db.py matches
  python inspect_db.py pickup_status
"""

import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "foodresq.db"


def print_table(cols, rows):
    if not rows:
        print("  (Table has no records)")
        return

    clean_rows = []
    for r in rows:
        clean_rows.append([str(v)[:30] if v is not None else "NULL" for v in r])

    col_widths = [len(c) for c in cols]
    for r in clean_rows:
        for idx, val in enumerate(r):
            col_widths[idx] = min(32, max(col_widths[idx], len(val)))

    header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))
    sep = "-+-".join("-" * col_widths[i] for i in range(len(cols)))
    print(header)
    print(sep)
    for r in clean_rows:
        print(" | ".join(r[i].ljust(col_widths[i]) for i in range(len(r))))


def main():
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()

    integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]

    all_tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

    args = sys.argv[1:]
    if not args:
        print("=" * 70)
        print(f"FOODRESQ AI — SQLITE DATABASE SUMMARY (Status: {integrity.upper()})")
        print("=" * 70)
        print(f"Database File: {DB_PATH}\n")
        print(f"{'Table Name':<25} | {'Records':<10} | {'Columns':<40}")
        print("-" * 25 + "-+-" + "-" * 10 + "-+-" + "-" * 40)
        for t in all_tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = [c[1] for c in cursor.execute(f"PRAGMA table_info({t})").fetchall()]
            cols_str = ", ".join(cols[:5]) + ("..." if len(cols) > 5 else "")
            print(f"{t:<25} | {count:<10} | {cols_str:<40}")

        print("\nTip: View specific table records by running:")
        print("  python inspect_db.py users")
        print("  python inspect_db.py surplus_food")
        print("  python inspect_db.py matches")
        print("  python inspect_db.py pickup_status")
        print("  python inspect_db.py ngos")
    else:
        target = args[0].lower().strip()
        if target not in all_tables:
            print(f"Error: Table '{target}' not found. Available tables: {', '.join(all_tables)}")
        else:
            count = cursor.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
            cursor.execute(f"SELECT * FROM {target} LIMIT 50")
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            print("=" * 80)
            print(f"TABLE: {target.upper()} (Total Records: {count})")
            print("=" * 80)
            print_table(cols, rows)

    con.close()


if __name__ == "__main__":
    main()

