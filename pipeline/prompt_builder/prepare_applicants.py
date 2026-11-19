"""Add the money columns to experiment/applicants/applicants.csv.

Run from the repository root:
  python -m pipeline.prompt_builder.prepare_applicants                      (recompute in place)
  python -m pipeline.prompt_builder.prepare_applicants path/to/part1 ...   (merge packages with an applicants_full.csv each)
"""
import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "experiment" / "applicants" / "applicants.csv"
AED_PER_EUR = 4.2
EUR_PER_DAY = 70
DERIVED = ["savings_aed", "net_income_aed", "savings_eur", "required_eur", "funds_cover_stay"]


def add_money(row):
    row = {k: v for k, v in row.items() if k not in DERIVED}
    savings_eur = round(int(row["savings"]) / AED_PER_EUR)
    required_eur = EUR_PER_DAY * int(row["stay_days"])
    return {**row, "savings_aed": f"{int(row['savings']):,}", "net_income_aed": f"{int(row['net_income']):,}",
            "savings_eur": f"{savings_eur:,}", "required_eur": f"{required_eur:,}",
            "funds_cover_stay": "yes" if savings_eur >= required_eur else "no"}


def main(folders):
    files = [Path(folder) / "applicants_full.csv" for folder in folders] or [OUT]
    rows = []
    for path in files:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows += [add_money(r) for r in csv.DictReader(f)]
    ids = [r["applicant_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("applicant_id values are not unique")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} applicants -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
