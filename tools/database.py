"""
database.py

SQLite Database Tool
Used by Gemini Function Calling.
"""

import sqlite3
import os


DATABASE_PATH = os.path.join(
    "database.db"
)


def database_query(sql_query: str) -> str:
    """
    Executes SQL queries
    on the local SQLite database.
    """

    print("\n[Database Tool Called]")

    try:

        if not os.path.exists(DATABASE_PATH):
            return "Database not found."

        connection = sqlite3.connect(DATABASE_PATH)

        cursor = connection.cursor()

        cursor.execute(sql_query)

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ] if cursor.description else []

        connection.close()

        if not rows:
            return "No records found."

        formatted_rows = []

        for row in rows:

            employee = []

            for column, value in zip(columns, row):

                employee.append(
                    f"{column}: {value}"
                )

            formatted_rows.append(
                "\n".join(employee)
            )

        return "\n\n".join(formatted_rows)

    except Exception as e:

        return (
            f"Database Error:\n{e}"
        )