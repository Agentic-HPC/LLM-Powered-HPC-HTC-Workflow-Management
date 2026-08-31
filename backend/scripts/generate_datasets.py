"""
SUPERSEDED: this script generates synthetic placeholder data. The project
now ships with real datasets (data/employees.csv, data/weather.csv,
sourced from real employee-attrition and hourly-weather data). Use
scripts/scale_datasets.py instead if you need larger versions for
benchmarking. This file is kept only as a reference/fallback in case you
want to regenerate purely synthetic data for some other reason.

Generates sample datasets used to exercise the platform end-to-end:
  - data/employees.csv  (500 rows: department, salary, hire_date, performance)
  - data/weather.csv    (6 years of daily weather: date, city, temp, precip)

Run: python scripts/generate_datasets.py
"""
import os
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Support"]
CITIES = ["New York", "London", "Tokyo", "Sydney", "Berlin", "Bengaluru"]


def generate_employees(n: int = 500) -> pd.DataFrame:
    rows = []
    start = date(2018, 1, 1)
    for i in range(n):
        dept = random.choice(DEPARTMENTS)
        base_salary = {
            "Engineering": 95000, "Sales": 70000, "Marketing": 68000,
            "HR": 60000, "Finance": 85000, "Operations": 62000, "Support": 55000,
        }[dept]
        salary = round(base_salary * random.uniform(0.8, 1.35), 2)
        hire_date = start + timedelta(days=random.randint(0, 365 * 6))
        rows.append({
            "employee_id": 1000 + i,
            "department": dept,
            "salary": salary,
            "hire_date": hire_date.isoformat(),
            "performance_score": round(random.uniform(2.0, 5.0), 2),
            "years_experience": random.randint(0, 20),
            "remote": random.choice([True, False]),
        })
    return pd.DataFrame(rows)


def generate_weather(years: int = 6) -> pd.DataFrame:
    rows = []
    end = date.today()
    start = date(end.year - years, end.month, end.day)
    d = start
    city_base_temp = {"New York": 12, "London": 11, "Tokyo": 16, "Sydney": 18, "Berlin": 10, "Bengaluru": 24}

    while d <= end:
        for city in CITIES:
            seasonal = 10 * ((d.timetuple().tm_yday / 365.0 - 0.5) ** 2) * -4
            temp = round(city_base_temp[city] + seasonal + random.uniform(-4, 4), 1)
            precip = round(max(0, random.gauss(2.5, 3.0)), 1)
            rows.append({"date": d.isoformat(), "city": city, "temperature_c": temp, "precipitation_mm": precip})
        d += timedelta(days=7)  # weekly sampling keeps file size reasonable

    return pd.DataFrame(rows)


def main():
    employees = generate_employees()
    employees_path = os.path.join(OUT_DIR, "employees.csv")
    employees.to_csv(employees_path, index=False)
    print(f"Wrote {len(employees)} rows -> {employees_path}")

    weather = generate_weather()
    weather_path = os.path.join(OUT_DIR, "weather.csv")
    weather.to_csv(weather_path, index=False)
    print(f"Wrote {len(weather)} rows -> {weather_path}")


if __name__ == "__main__":
    main()
