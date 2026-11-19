"""Read the score or recommendation and the reason out of every raw answer.

Run from the repository root: python -m pipeline.answers.parse_answers
Writes results/processed/answers.csv, one row per answer to the current prompts.
Answers to an older version of a prompt (another prompt_hash) are left out and counted.
"""
import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results"
COLUMNS = ["model", "run", "temperature", "top_p", "top_k", "prompt_id", "repeat", "variant", "wording",
           "applicant_id", "country", "output", "status", "visa_score", "granted", "reason"]


NUMBER = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*100)?\s*$")


def score(answer, key="visa_score"):
    value = answer[key]
    if isinstance(value, bool):
        raise ValueError(value)
    if isinstance(value, str):
        match = NUMBER.match(value)
        if not match:
            raise ValueError(value)
        value = match[1]
    value = float(value)
    if not 0 <= value <= 100:
        raise ValueError(value)
    return value


def reason(answer):
    return str(answer.get("reason") or "").strip()


def read_score(answer):
    return {"visa_score": score(answer), "reason": reason(answer)}


def read_risk(answer):
    return {"visa_score": 100 - score(answer, "risk_score"), "reason": reason(answer)}


def read_score_only(answer):
    return {"visa_score": score(answer)}


def read_binary(answer):
    decision = str(answer["recommendation"]).strip().lower()
    if decision not in ("grant", "refuse"):
        raise ValueError(decision)
    return {"granted": int(decision == "grant"), "reason": reason(answer)}


FORMATS = {"score": read_score, "risk": read_risk, "score_only": read_score_only, "binary": read_binary}


DECODER = json.JSONDecoder(strict=False)


def json_objects(text):
    """Every JSON object in the text, last one first."""
    found = []
    for start in [i for i, c in enumerate(text) if c == "{"]:
        try:
            value, _ = DECODER.raw_decode(text, start)
        except ValueError:
            continue
        if isinstance(value, dict):
            found.append(value)
    return reversed(found)


def strip_thinking(text):
    if "</think>" in text:
        return text.rsplit("</think>", 1)[1]
    if "<think>" in text:
        return ""
    return text


def parse(text, output="score"):
    for answer in json_objects(strip_thinking(text)):
        try:
            values = FORMATS[output](answer)
        except (ValueError, KeyError, TypeError):
            continue
        return {"status": "ok", "visa_score": "", "granted": "", "reason": "", **values}
    return {"status": "unreadable", "visa_score": "", "granted": "", "reason": ""}


def latest_answers(path):
    answers = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not record["error"]:
                answers[(record["prompt_id"], record["repeat"])] = record
    return answers.values()


def main():
    with open(REPO / "experiment" / "prompts" / "prompts.csv", encoding="utf-8") as f:
        prompts = {p["prompt_id"]: p for p in csv.DictReader(f)}
    # A run's answers can be spread over a main file and part files; keep one answer per call.
    records, outdated = {}, 0
    for path in sorted((RESULTS / "raw").glob("*.jsonl")):
        for record in latest_answers(path):
            prompt = prompts.get(record["prompt_id"])
            if prompt is None or prompt["prompt_hash"] != record["prompt_hash"]:
                outdated += 1
                continue
            records[(record["model"], record["run"], record["prompt_id"], record["repeat"])] = record
    rows = []
    for record in records.values():
        prompt = prompts[record["prompt_id"]]
        parsed = parse(record["text"], prompt["output"])
        if record["finish_reason"] == "length" and parsed["status"] != "ok":
            parsed["status"] = "too_long"
        rows.append({**{k: record[k] for k in ("model", "run", "temperature", "top_p", "top_k", "prompt_id", "repeat")},
                     **{k: prompt[k] for k in ("variant", "wording", "applicant_id", "country", "output")},
                     **parsed})
    out = RESULTS / "processed" / "answers.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} answers, {sum(r['status'] == 'ok' for r in rows)} readable, "
          f"{outdated} to older prompt versions left out -> {out}")


if __name__ == "__main__":
    main()
