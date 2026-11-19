"""Fill the judge prompt for every readable answer, with the nationality hidden.

Run from the repository root: python -m pipeline.judge.build_judge_prompts
Writes results/processed/judge_prompts.csv.
"""
import csv
import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / "experiment"
RESULTS = REPO / "results"
RESIDENCE = "United Arab Emirates"
OTHER_NAMES = {"Myanmar": ["Burma"], "Palestine": ["Gaza", "West Bank"]}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def hide(text, word, placeholder):
    return re.sub(rf"\b{re.escape(word)}\w*", placeholder, text, flags=re.I)


def mask(text, nationality):
    words = [(nationality["demonym"], "[NATIONALITY]")]
    if nationality["country"] != RESIDENCE:
        words += [(name, "[PASSPORT COUNTRY]")
                  for name in [nationality["country"], *OTHER_NAMES.get(nationality["country"], [])]]
    for word, placeholder in sorted(words, key=lambda w: -len(w[0])):
        text = hide(text, word, placeholder)
    return text


def judge_id(answer):
    return f"{answer['model']}__{answer['prompt_id']}__{answer['repeat']}"


def main():
    template = (EXPERIMENT / "judge" / "judge_prompt.txt").read_text(encoding="utf-8")
    prompts = {p["prompt_id"]: p["user"] for p in read_csv(EXPERIMENT / "prompts" / "prompts.csv")}
    nationalities = {n["country"]: n for n in read_csv(EXPERIMENT / "countries" / "nationalities.csv")}
    rows = []
    for answer in read_csv(RESULTS / "processed" / "answers.csv"):
        if answer["run"] != "main" or answer["status"] != "ok" or not answer["reason"]:
            continue
        nationality = nationalities[answer["country"]]
        prompt = template.replace("{application}", mask(prompts[answer["prompt_id"]], nationality))
        prompt = prompt.replace("{reason}", mask(answer["reason"], nationality))
        rows.append({"prompt_id": judge_id(answer), "repeats": 1,
                     "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16], "system": "", "user": prompt})
    out = RESULTS / "processed" / "judge_prompts.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["prompt_id", "repeats", "prompt_hash", "system", "user"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} judge prompts -> {out}")


if __name__ == "__main__":
    main()
