import csv
import json
import os
from pathlib import Path

YEAR = 2026
LOCID = "900"
VARIANT = "Medium"
SECONDS_PER_YEAR = 365.25 * 86400

POPULATION_CSV = "WPP2024_TotalPopulationBySex.csv"
BIRTH_RATE_CSV = "WPP2024_FERT_F01_CRUDE_BIRTH_RATE.csv"
DEATH_RATE_CSV = "WPP2024_MORT_F01_CRUDE_DEATH_RATE.csv"


def get_data_dir(data_dir=None):
    if data_dir is not None:
        return Path(data_dir)
    configured = os.getenv("WPP_DATA_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent


def load_value(path, value_field, year=YEAR):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (
                row.get("LocID") == LOCID and
                row.get("Variant") == VARIANT and
                int(row.get("Time")) == year
            ):
                return float(row[value_field])

    raise ValueError(f"Value not found in {path} for {year}, {LOCID}, {VARIANT}")


def build_anchor(year=YEAR, data_dir=None):
    data_dir = get_data_dir(data_dir)
    population = load_value(data_dir / POPULATION_CSV, "PopTotal", year=year)
    cbr = load_value(data_dir / BIRTH_RATE_CSV, "CBR", year=year)
    cdr = load_value(data_dir / DEATH_RATE_CSV, "CDR", year=year)

    births_per_second = (cbr / 1000) * (population / SECONDS_PER_YEAR)
    deaths_per_second = (cdr / 1000) * (population / SECONDS_PER_YEAR)

    anchor = {
        "baseline_population": population,
        "baseline_timestamp": f"{year}-01-01T00:00:00Z",
        "births_per_second": births_per_second,
        "deaths_per_second": deaths_per_second,
        "source": "UN WPP 2024 Medium Variant",
        "last_anchor_year": int(year),
    }
    return anchor


def main():
    print(json.dumps(build_anchor(), indent=2))


if __name__ == "__main__":
    main()