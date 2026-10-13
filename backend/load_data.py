"""Create the Supabase schema and load the cleaned medicine CSV."""

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path
from statistics import median

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

try:
    from . import queries
except ImportError:
    import queries

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "medicine_data_cleaned.csv"


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def split_effects(value: str) -> list[str]:
    return list(dict.fromkeys(part.strip() for part in (value or "").split(",") if part.strip()))


def load(csv_path: Path, replace: bool = False, schema_only: bool = False) -> None:
    load_dotenv(ROOT / "backend" / ".env")
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise SystemExit("DATABASE_URL is required in backend/.env (Supabase Settings > Database > URI)")

    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(queries.CREATE_SCHEMA.sql)
            if schema_only:
                conn.commit()
                print("Supabase schema created successfully.")
                return
            cur.execute(queries.COUNT_MEDICINES.sql)
            existing = cur.fetchone()["count"]
            if existing and not replace:
                raise SystemExit(f"Database already contains {existing} medicines. Re-run with --replace to reload.")
            if replace:
                cur.execute(queries.TRUNCATE_ALL.sql)

            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

            grouped: dict[str, list[float]] = defaultdict(list)
            for row in rows:
                grouped[row["product_manufactured"]].append(float(row["price_clean"]))
            manufacturer_values = [
                (name, len(prices), sum(prices) / len(prices), median(prices))
                for name, prices in grouped.items()
            ]
            cur.executemany(queries.INSERT_MANUFACTURER.sql, manufacturer_values)

            cur.execute(queries.GET_MANUFACTURER_IDS.sql)
            manufacturer_ids = {row["name"]: row["id"] for row in cur.fetchall()}

            medicine_values = []
            side_effect_values = []
            for index, row in enumerate(rows, 1):
                medicine_values.append((
                    index, row["product_name"], row["sub_category"], row["salt_composition"], row["primary_salt"],
                    int(row["num_ingredients"]), float(row["price_clean"]), as_bool(row["is_price_outlier"]),
                    manufacturer_ids[row["product_manufactured"]], row["medicine_desc"],
                    int(row["num_side_effects"]), int(row["num_interactions"]),
                    as_bool(row["has_life_threatening_interaction"]),
                ))
                for effect in split_effects(row["side_effects"]):
                    side_effect_values.append((index, effect))
            print(f"Batch inserting {len(medicine_values):,} medicines...")
            cur.executemany(queries.INSERT_MEDICINE.sql, medicine_values)
            cur.execute(queries.SET_MEDICINE_SEQUENCE.sql)
            print(f"Batch inserting {len(side_effect_values):,} normalized side-effect links...")
            cur.executemany(queries.INSERT_SIDE_EFFECT.sql, side_effect_values)
            conn.commit()
            print(f"Loaded {len(rows):,} medicines, {len(grouped):,} manufacturers, and {len(side_effect_values):,} side-effect links into Supabase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--replace", action="store_true", help="Explicitly replace existing rows")
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args()
    load(args.csv, args.replace, args.schema_only)
