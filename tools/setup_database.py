"""
Sets up the benchmark SQLite database with synthetic tables.
Tables: sales, employees, weather, inventory, customers, orders.
Run standalone: python -m tools.setup_database
"""

import sqlite3
import random
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from config import SQLITE_DB_PATH, DATASETS_DIR

random.seed(42)  # Reproducibility


def create_database():
    """Create and populate the benchmark SQLite database."""
    os.makedirs(SQLITE_DB_PATH.parent, exist_ok=True)

    # Remove existing DB for a clean start
    if SQLITE_DB_PATH.exists():
        SQLITE_DB_PATH.unlink()

    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    c = conn.cursor()

    _create_sales(c)
    _create_employees(c)
    _create_weather(c)
    _create_inventory(c)
    _create_customers(c)
    _create_orders(c)

    conn.commit()
    conn.close()
    print(f"Database created at {SQLITE_DB_PATH}")


def _create_sales(c):
    """Sales data: 1000 rows spanning 12 months."""
    c.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            date TEXT,
            product TEXT,
            region TEXT,
            revenue REAL,
            units_sold INTEGER
        )
    """)

    products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Service Pro", "Service Basic"]
    regions = ["North", "South", "East", "West"]
    base_date = datetime(2025, 1, 1)

    rows = []
    for i in range(1, 1001):
        date = base_date + timedelta(days=random.randint(0, 364))
        product = random.choice(products)
        region = random.choice(regions)
        units = random.randint(1, 50)
        price_map = {
            "Widget A": 25.0, "Widget B": 45.0, "Gadget X": 120.0,
            "Gadget Y": 89.0, "Service Pro": 200.0, "Service Basic": 75.0,
        }
        revenue = round(units * price_map[product] * random.uniform(0.8, 1.2), 2)
        rows.append((i, date.strftime("%Y-%m-%d"), product, region, revenue, units))

    c.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?)", rows)

    # Also export as CSV for data analysis tasks
    _export_csv("sales_data.csv", ["id", "date", "product", "region", "revenue", "units_sold"], rows)


def _create_employees(c):
    """Employee data: 500 rows."""
    c.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary REAL,
            years_experience INTEGER,
            performance_score REAL
        )
    """)

    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
                   "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
                   "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                  "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore",
                  "Jackson", "Martin", "Lee", "Thompson", "White", "Harris"]

    salary_ranges = {
        "Engineering": (70000, 150000), "Marketing": (55000, 110000),
        "Sales": (50000, 120000), "HR": (50000, 95000),
        "Finance": (60000, 130000), "Operations": (45000, 100000),
    }

    rows = []
    for i in range(1, 501):
        dept = random.choice(departments)
        years = random.randint(0, 30)
        lo, hi = salary_ranges[dept]
        salary = round(random.uniform(lo, hi) + years * 1500, 2)
        score = round(min(5.0, max(1.0, random.gauss(3.5, 0.8))), 2)
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        rows.append((i, name, dept, salary, years, score))

    c.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", rows)
    _export_csv("employee_data.csv", ["id", "name", "department", "salary", "years_experience", "performance_score"], rows)


def _create_weather(c):
    """Weather data: 365 days × 5 cities = 1825 rows."""
    c.execute("""
        CREATE TABLE weather (
            id INTEGER PRIMARY KEY,
            date TEXT,
            city TEXT,
            temperature REAL,
            humidity REAL,
            precipitation REAL
        )
    """)

    cities = {
        "New York": (30, 85, 50), "Los Angeles": (55, 90, 20),
        "Chicago": (20, 80, 45), "Houston": (45, 95, 55),
        "Phoenix": (50, 110, 10),
    }
    base_date = datetime(2025, 1, 1)

    rows = []
    idx = 1
    for day_offset in range(365):
        date = base_date + timedelta(days=day_offset)
        day_of_year = date.timetuple().tm_yday
        # Seasonal variation
        season_factor = 0.5 * (1 + __import__("math").sin(2 * 3.14159 * (day_of_year - 80) / 365))
        for city, (lo, hi, precip_base) in cities.items():
            temp = round(lo + (hi - lo) * season_factor + random.gauss(0, 5), 1)
            humidity = round(min(100, max(10, random.gauss(60, 15))), 1)
            precipitation = round(max(0, random.expovariate(1 / precip_base) * (0.3 + 0.7 * random.random())), 2)
            rows.append((idx, date.strftime("%Y-%m-%d"), city, temp, humidity, precipitation))
            idx += 1

    c.executemany("INSERT INTO weather VALUES (?,?,?,?,?,?)", rows)
    _export_csv("weather_data.csv", ["id", "date", "city", "temperature", "humidity", "precipitation"], rows)


def _create_inventory(c):
    """Inventory data: 200 items across warehouses."""
    c.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            warehouse TEXT,
            quantity INTEGER,
            unit_cost REAL,
            last_restocked TEXT
        )
    """)

    products = [f"SKU-{i:04d}" for i in range(1, 201)]
    warehouses = ["Warehouse-East", "Warehouse-West", "Warehouse-Central"]
    base_date = datetime(2025, 1, 1)

    rows = []
    for i, prod in enumerate(products, 1):
        wh = random.choice(warehouses)
        qty = random.randint(0, 500)
        cost = round(random.uniform(5, 500), 2)
        restock = base_date + timedelta(days=random.randint(0, 180))
        rows.append((i, prod, wh, qty, cost, restock.strftime("%Y-%m-%d")))

    c.executemany("INSERT INTO inventory VALUES (?,?,?,?,?,?)", rows)


def _create_customers(c):
    """Customer data: 300 customers."""
    c.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            country TEXT,
            signup_date TEXT,
            tier TEXT
        )
    """)

    countries = ["US", "UK", "Germany", "France", "Japan", "Canada", "Australia", "Brazil"]
    tiers = ["free", "basic", "premium", "enterprise"]
    base_date = datetime(2023, 1, 1)

    rows = []
    for i in range(1, 301):
        name = f"Customer_{i:03d}"
        email = f"customer{i}@example.com"
        country = random.choice(countries)
        signup = base_date + timedelta(days=random.randint(0, 730))
        tier = random.choices(tiers, weights=[40, 30, 20, 10])[0]
        rows.append((i, name, email, country, signup.strftime("%Y-%m-%d"), tier))

    c.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", rows)


def _create_orders(c):
    """Order data: 800 orders."""
    c.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product TEXT,
            quantity INTEGER,
            total_amount REAL,
            order_date TEXT,
            status TEXT
        )
    """)

    products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Service Pro", "Service Basic"]
    statuses = ["pending", "shipped", "delivered", "cancelled"]
    base_date = datetime(2025, 1, 1)

    rows = []
    for i in range(1, 801):
        cust_id = random.randint(1, 300)
        product = random.choice(products)
        qty = random.randint(1, 10)
        total = round(qty * random.uniform(25, 250), 2)
        order_date = base_date + timedelta(days=random.randint(0, 364))
        status = random.choices(statuses, weights=[15, 25, 50, 10])[0]
        rows.append((i, cust_id, product, qty, total, order_date.strftime("%Y-%m-%d"), status))

    c.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", rows)


def _export_csv(filename, headers, rows):
    """Export data as CSV alongside the database."""
    csv_path = DATASETS_DIR / filename
    os.makedirs(csv_path.parent, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  Exported CSV: {csv_path}")


if __name__ == "__main__":
    create_database()
