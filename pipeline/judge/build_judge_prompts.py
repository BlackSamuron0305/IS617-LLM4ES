"""Fill the judge prompt for every readable answer, with the nationality hidden.

Run from the repository root: python -m pipeline.judge.build_judge_prompts
Writes results/processed/judge_prompts.csv (one row per distinct judge prompt) and
results/processed/judge_links.csv (which judge prompt each answer uses).

With the nationality hidden, the same reason for the same application gives the same judge prompt,
whichever passport or repetition it came from. Such answers share one judge call (README: "identical
reasons for the same application can share one call"). A judge prompt's id is the fingerprint of its
text, so it stays the same when answers of more models are added later.
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


def share(filled):
    """filled: (answer id, judge prompt) pairs -> (one row per distinct prompt, one link per answer)."""
    rows, links = {}, []
    for answer_id, prompt in filled:
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        prompt_id = f"j{digest}"
        if prompt_id not in rows:
            rows[prompt_id] = {"prompt_id": prompt_id, "repeats": 1, "prompt_hash": digest, "system": "", "user": prompt}
        links.append({"answer_id": answer_id, "judge_prompt_id": prompt_id})
    return list(rows.values()), links


def filled_prompts():
    template = (EXPERIMENT / "judge" / "judge_prompt.txt").read_text(encoding="utf-8")
    prompts = {p["prompt_id"]: p["user"] for p in read_csv(EXPERIMENT / "prompts" / "prompts.csv")}
    nationalities = {n["country"]: n for n in read_csv(EXPERIMENT / "countries" / "nationalities.csv")}
    for answer in read_csv(RESULTS / "processed" / "answers.csv"):
        if answer["run"] != "main" or answer["status"] != "ok" or not answer["reason"]:
            continue
        nationality = nationalities[answer["country"]]
        prompt = template.replace("{application}", mask(prompts[answer["prompt_id"]], nationality))
        yield judge_id(answer), prompt.replace("{reason}", mask(answer["reason"], nationality))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows, links = share(filled_prompts())
    out = RESULTS / "processed" / "judge_prompts.csv"
    write_csv(out, rows, ["prompt_id", "repeats", "prompt_hash", "system", "user"])
    write_csv(RESULTS / "processed" / "judge_links.csv", links, ["answer_id", "judge_prompt_id"])
    print(f"{len(links)} answers, {len(rows)} distinct judge prompts -> {out}")


if __name__ == "__main__":
    main()
