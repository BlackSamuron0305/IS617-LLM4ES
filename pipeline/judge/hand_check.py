"""Hand check of the judge: the team codes a sample of reasons by hand, then the agreement with the judge is computed.

    python -m pipeline.judge.hand_check sample            # writes experiment/judge/hand_check/sheet.csv and key.csv
    python -m pipeline.judge.hand_check agreement         # reads every sheet_<name>.csv there and prints the agreement

Workflow: each team member copies sheet.csv to sheet_<name>.csv and fills the eight code columns with 1 (yes) or 0 (no),
following the questions in experiment/judge/README.md, without looking at key.csv. The sheet hides the model, the
nationality and the judge's codes. The application behind each reason is the row `applicant_id` of
experiment/applicants/applicants.csv.

Sample: per main model, 25 reasons at random and 25 among those the judge coded with any concern (so that the rarer
"yes" codes occur often enough to check), in random order. Fixed seed, so the sample can be rebuilt.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "experiment" / "judge" / "hand_check"
CODES = ["mentions_nationality", "nationality_as_concern", "ground_applies", "any_concern", "funds_concern", "funds_ok",
         "ties_concern", "unsupported_concern"]
MAIN = ["gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "qwen3-32b"]
PER_MODEL = 25


def sample(seed=617):
    codes = pd.read_csv(REPO / "results" / "processed" / "judge_codes.csv")
    answers = pd.read_csv(REPO / "results" / "processed" / "answers.csv",
                          usecols=["model", "run", "prompt_id", "repeat", "applicant_id", "variant", "reason"])
    df = codes.merge(answers[answers["run"] == "main"], on=["model", "prompt_id", "repeat"])
    df = df[df["model"].isin(MAIN)]
    rng = np.random.default_rng(seed)
    parts = []
    for model in MAIN:
        d = df[df["model"] == model]
        first = d.sample(PER_MODEL, random_state=rng.integers(1 << 31))
        rest = d[(d["any_concern"] == 1) & ~d.index.isin(first.index)]
        parts += [first, rest.sample(PER_MODEL, random_state=rng.integers(1 << 31))]
    picked = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    picked.insert(0, "item", range(1, len(picked) + 1))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = picked[["item", "applicant_id", "variant", "reason"]].copy()
    for code in CODES:
        sheet[code] = ""
    sheet.to_csv(OUT / "sheet.csv", index=False)
    picked[["item", "model", "prompt_id", "repeat", "applicant_id"] + CODES].to_csv(OUT / "key.csv", index=False)
    print(f"{len(sheet)} reasons -> {OUT / 'sheet.csv'} (and key.csv, not for the coders)")


def kappa(a, b):
    """Cohen's kappa of two 0/1 series. None when both raters give only one value."""
    a, b = np.asarray(a, int), np.asarray(b, int)
    observed = (a == b).mean()
    expected = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return None if expected == 1 else (observed - expected) / (1 - expected)


def agreement():
    key = pd.read_csv(OUT / "key.csv").set_index("item")
    sheets = sorted(OUT.glob("sheet_*.csv"))
    if not sheets:
        raise SystemExit(f"No filled sheets (sheet_<name>.csv) in {OUT}")
    rows = []
    for path in sheets:
        coder = pd.read_csv(path).set_index("item")
        for code in CODES:
            filled = coder[code].dropna()
            judge = key.loc[filled.index, code]
            rows.append({"coder": path.stem[6:], "code": code, "items": len(filled),
                         "agreement_%": round(100 * (filled.astype(int) == judge).mean(), 1),
                         "kappa": kappa(filled, judge), "judge_yes": int(judge.sum()), "coder_yes": int(filled.sum())})
    table = pd.DataFrame(rows)
    print(table.to_string(index=False))
    table.to_csv(OUT / "agreement.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=["sample", "agreement"])
    {"sample": sample, "agreement": agreement}[parser.parse_args().step]()
