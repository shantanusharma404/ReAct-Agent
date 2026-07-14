"""
create_db.py

Creates a sample SQLite database for the Database Tool.
"""

import sqlite3

DATABASE_NAME = "database.db"


def create_database():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
    DROP TABLE IF EXISTS employees
    """)

    cursor.execute("""
    CREATE TABLE employees (

        employee_id INTEGER PRIMARY KEY,

        name TEXT NOT NULL,

        age INTEGER,

        department TEXT,

        designation TEXT,

        salary INTEGER,

        experience INTEGER,

        city TEXT,

        email TEXT
    )
    """)

    employees = [

        (101, "Alice Johnson", 28, "HR", "HR Executive", 45000, 3, "New York", "alice@company.com"),

        (102, "Bob Smith", 35, "IT", "Software Engineer", 85000, 8, "Chicago", "bob@company.com"),

        (103, "Charlie Brown", 30, "Finance", "Financial Analyst", 65000, 6, "Boston", "charlie@company.com"),

        (104, "David Wilson", 41, "IT", "Senior Software Engineer", 125000, 15, "Seattle", "david@company.com"),

        (105, "Emma Thomas", 27, "Marketing", "Marketing Executive", 52000, 4, "Los Angeles", "emma@company.com"),

        (106, "Frank Miller", 45, "Management", "Project Manager", 145000, 18, "Austin", "frank@company.com"),

        (107, "Grace Lee", 31, "IT", "Data Scientist", 98000, 7, "San Francisco", "grace@company.com"),

        (108, "Henry Walker", 29, "Sales", "Sales Executive", 60000, 5, "Houston", "henry@company.com"),

        (109, "Isabella White", 38, "Finance", "Finance Manager", 135000, 12, "Dallas", "isabella@company.com"),

        (110, "James Clark", 33, "IT", "DevOps Engineer", 92000, 9, "Denver", "james@company.com")

    ]

    cursor.executemany("""
    INSERT INTO employees
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)

    connection.commit()
    connection.close()

    print("Database created successfully!")


if __name__ == "__main__":
    create_database()