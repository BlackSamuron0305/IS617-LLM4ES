"""Build every prompt: prompt x wording x applicant x nationality, as planned in run_plan.csv.

Run from the repository root: python -m pipeline.prompt_builder.build_prompts
"""
import csv
import hashlib
import re
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[2] / "experiment"
PROMPTS = EXPERIMENT / "prompts"
BLANK = re.compile(r"\{\{(applicant|nationality)\.(\w+)\}\}")
SECTION = re.compile(r"^=+\s*$", flags=re.M)
OUTPUTS = {"score", "risk", "score_only", "binary"}
COLUMNS = ["prompt_id", "variant", "wording", "applicant_id", "country", "output", "repeats", "prompt_hash", "system", "user"]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_prompt(text):
    parts = [p.strip() for p in SECTION.split(text)]
    sections = dict(zip(parts[1::2], parts[2::2]))
    wordings = {int(re.search(r"WORDING (\d+)", title)[1]): body
                for title, body in sections.items() if title.startswith("USER MESSAGE")}
    return sections["SYSTEM PROMPT"], wordings


def load_prompts(folder=PROMPTS):
    files = {"base": folder / "base_prompt.txt", **{f.stem: f for f in sorted((folder / "prompt_variants").glob("*.txt"))}}
    plan = {row["prompt"]: row for row in read_csv(folder / "run_plan.csv")}
    if set(files) != set(plan):
        raise ValueError(f"run_plan.csv and the prompt files do not match: "
                         f"no row for {sorted(set(files) - set(plan))}, no file for {sorted(set(plan) - set(files))}")
    prompts = {}
    for name, path in files.items():
        if plan[name]["output"] not in OUTPUTS:
            raise ValueError(f"{name}: unknown output {plan[name]['output']!r}, expected one of {sorted(OUTPUTS)}")
        system, wordings = split_prompt(path.read_text(encoding="utf-8"))
        for w in map(int, plan[name]["wordings"].split()):
            if "{application}" not in wordings[w]:
                raise ValueError(f"{name}, wording {w}: no {{application}} slot")
            prompts[(name, w)] = {"system": system, "user": wordings[w], "output": plan[name]["output"],
                                  "repeats": int(plan[name]["repeats"])}
    return prompts


def fill(template, applicant, nationality):
    values = {"applicant": applicant, "nationality": nationality}
    text = BLANK.sub(lambda m: values[m[1]][m[2]], template)
    if "{{" in text:
        raise ValueError(f"unknown blank in the application template: {re.findall(r'{{.*?}}', text)}")
    return text


def build(prompts, application, applicants, nationalities):
    if "{{nationality." not in application:
        raise ValueError("the application template has no {{nationality.…}} blank")
    rows = []
    for (name, wording), p in prompts.items():
        for a in applicants:
            for n in nationalities:
                user = p["user"].replace("{application}", fill(application, a, n))
                rows.append({
                    "prompt_id": f"{name}__w{wording}__{a['applicant_id']}__{n['country']}",
                    "variant": name,
                    "wording": wording,
                    "applicant_id": a["applicant_id"],
                    "country": n["country"],
                    "output": p["output"],
                    "repeats": p["repeats"],
                    "prompt_hash": hashlib.sha256(f"{p['system']}\n\n{user}".encode()).hexdigest()[:16],
                    "system": p["system"],
                    "user": user,
                })
    return rows


def main():
    rows = build(
        load_prompts(),
        (EXPERIMENT / "applicants" / "application_template.txt").read_text(encoding="utf-8").strip(),
        read_csv(EXPERIMENT / "applicants" / "applicants.csv"),
        read_csv(EXPERIMENT / "countries" / "nationalities.csv"),
    )
    with open(PROMPTS / "prompts.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} prompts written to {PROMPTS / 'prompts.csv'}")


if __name__ == "__main__":
    main()
