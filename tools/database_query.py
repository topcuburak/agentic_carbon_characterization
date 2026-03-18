"""
SQLite database query tool.
Executes SQL on the pre-populated benchmark database.
"""

import sqlite3
import json
from config import SQLITE_DB_PATH

_connection: sqlite3.Connection | None = None


def _get_connection() -> sqlite3.Connection:
    """Get or create a persistent database connection."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(SQLITE_DB_PATH))
        _connection.row_factory = sqlite3.Row
    return _connection


def reset_connection():
    """Close and reset the database connection (for test isolation)."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def database_query(sql: str) -> str:
    """
    Execute a SQL query on the benchmark SQLite database.
    SELECT queries return rows as JSON list of dicts.
    Other queries return the number of affected rows.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        sql_stripped = sql.strip().upper()

        if sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH") or sql_stripped.startswith("PRAGMA"):
            cursor.execute(sql)
            rows = cursor.fetchall()

            if not rows:
                return "Query returned 0 rows."

            result = [dict(row) for row in rows]

            # Truncate large result sets
            if len(result) > 100:
                output = json.dumps(result[:100], indent=2, default=str)
                return f"{output}\n\n... [{len(result)} total rows, showing first 100]"

            return json.dumps(result, indent=2, default=str)

        else:
            # DML statements
            cursor.execute(sql)
            conn.commit()
            return f"Query executed successfully. Rows affected: {cursor.rowcount}"

    except sqlite3.Error as e:
        return f"SQL Error: {e}"
    except Exception as e:
        return f"Error executing query: {e}"
