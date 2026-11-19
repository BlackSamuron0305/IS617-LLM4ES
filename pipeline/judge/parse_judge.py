"""Read the yes/no codes out of every raw judge answer.

Run from the repository root: python -m pipeline.judge.parse_judge --judge olmo-3.1-32b-instruct
Writes results/processed/judge_codes.csv: one row per judged answer, codes as 1 (yes) and 0 (no).
Only the latest answer to the current version of each judge prompt is used.
"""
import argparse
import csv
from pathlib import Path

from pipeline.answers.parse_answers import json_objects, strip_thinking
from pipeline.runner.run_model import read_records

RESULTS = Path(__file__).resolve().parents[2] / "results"
CODES = ["mentions_nationality", "nationality_as_concern", "ground_applies", "any_concern",
         "funds_concern", "funds_ok", "ties_concern", "unsupported_concern"]


def parse(text):
    for answer in json_objects(strip_thinking(text)):
        values = [str(answer.get(code, "")).strip().lower() for code in CODES]
        if all(v in ("yes", "no") for v in values):
            return {code: int(v == "yes") for code, v in zip(CODES, values)} | {"evidence": answer.get("evidence", "")}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True)
    args = ap.parse_args()

    with open(RESULTS / "processed" / "judge_prompts.csv", encoding="utf-8", newline="") as f:
        current = {p["prompt_id"]: p["prompt_hash"] for p in csv.DictReader(f)}
    latest = {}
    for record in read_records(RESULTS / "raw" / "judge" / f"{args.judge}.jsonl"):
        if not record["error"] and current.get(record["prompt_id"]) == record["prompt_hash"]:
            latest[record["prompt_id"]] = record

    rows, unreadable = [], 0
    for judge_id, record in latest.items():
        codes = parse(record["text"])
        if codes is None:
            unreadable += 1
            continue
        model, rest = judge_id.split("__", 1)
        prompt_id, repeat = rest.rsplit("__", 1)
        rows.append({"judge": args.judge, "model": model, "prompt_id": prompt_id, "repeat": repeat, **codes})
    out = RESULTS / "processed" / "judge_codes.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["judge", "model", "prompt_id", "repeat", *CODES, "evidence"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} coded, {unreadable} unreadable, {len(current) - len(latest)} not judged yet -> {out}")


if __name__ == "__main__":
    main()
