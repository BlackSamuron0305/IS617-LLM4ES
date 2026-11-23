"""Send every prompt to a model served by vLLM and save the raw answers.

Run from the repository root, with the server address in BASE_URL:
  python -m pipeline.runner.run_model --model qwen3-32b
  python -m pipeline.runner.run_model --model qwen3-32b --tag t0 --temperature 0 --repeats 1
  python -m pipeline.runner.run_model --model olmo-3.1-32b-instruct --judge
  python -m pipeline.runner.run_model --model qwen3-32b --check-done   (exit 0 when nothing is left)
  python -m pipeline.runner.run_model --model qwen3-32b --part 3 --parts 18   (one of 18 parts, for parallel jobs)
  python -m pipeline.runner.run_model --model olmo-3.1-32b-instruct --judge --part 3 --parts 24

With --parts, every prompt (with all its repeats) belongs to exactly one part, and each part writes its
own file, results/raw/<model>.part<i>of<n>.jsonl (judge: results/raw/judge/<judge>.part<i>of<n>.jsonl),
so parts can run at the same time on different GPUs. The split depends only on the prompt_id, so prompts
added later (a new model's answers to judge) do not move the old ones to another part.
Answers already in the main file or in any of its part files count as done.
"""
import argparse
import csv
import json
import os
import sys
import threading
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "experiment" / "config"
RESULTS = REPO / "results"
MAX_ERRORS_IN_A_ROW = 50
PROMPT_ROOM = 2500


def read_csv(path):
    return list(iter_csv(path))


def iter_csv(path):
    """Row by row, so a big file (the judge prompts) can be filtered without holding it all in memory."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def load_model(alias):
    for row in read_csv(CONFIG / "models.csv"):
        if row["alias"] == alias:
            return row
    raise SystemExit(f"unknown model {alias!r} in {CONFIG / 'models.csv'}")


def load_settings():
    return {row["setting"]: row["value"] for row in read_csv(CONFIG / "run_settings.csv")}


def read_records(path):
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except ValueError:
                pass
    return records


def answer_files(name, folder=None):
    """The main file of a run and all its part files."""
    raw = RESULTS / "raw" / (folder or "")
    return [raw / f"{name}.jsonl"] + sorted(raw.glob(f"{name}.part*of*.jsonl"))


def done_keys(paths):
    return {(r["prompt_id"], r["repeat"], r["prompt_hash"])
            for path in paths for r in read_records(path) if not r["error"]}


def in_part(prompt_id, part, parts):
    """Stable split of the prompts into parts 1..parts by prompt_id."""
    return zlib.crc32(prompt_id.encode("utf-8")) % parts == part - 1


def pending(prompts, done, repeats=None):
    return [(p, k) for p in prompts for k in range(1, (repeats or int(p["repeats"])) + 1)
            if (p["prompt_id"], k, p["prompt_hash"]) not in done]


def request(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)


def call(base_url, body):
    answer = request(f"{base_url}/chat/completions", body)
    choice = answer["choices"][0]
    usage = answer.get("usage") or {}
    return (choice["message"].get("content") or "", choice["finish_reason"],
            usage.get("prompt_tokens"), usage.get("completion_tokens"))


def check_server(base_url, served_name, model, max_tokens):
    served = {m["id"]: m for m in request(f"{base_url}/models")["data"]}
    if served_name not in served:
        raise SystemExit(f"the server serves {sorted(served)}, not {served_name!r}")
    weights = Path(served[served_name].get("root") or served_name).name.lower()
    expected = model["model_id"].split("/")[-1].lower()
    if not (model["alias"].startswith(weights) or weights == expected):
        raise SystemExit(f"the server runs the weights {weights!r}, but {model['alias']!r} needs {model['model_id']}")
    limit = served[served_name].get("max_model_len")
    if limit and max_tokens + PROMPT_ROOM > limit:
        raise SystemExit(f"max_tokens {max_tokens} does not fit the server's --max-model-len {limit}; "
                         f"start it with VLLM_ARGS='--max-model-len {max_tokens + PROMPT_ROOM}' or more")
    return weights


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--judge", action="store_true", help="run the judge prompts instead of the main prompts")
    ap.add_argument("--tag", default="main", help="name of a run with other settings; it gets its own file")
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--top-p", type=float)
    ap.add_argument("--top-k", type=int)
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--variant", help="only the prompts of this variant")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--limit", type=int, help="only the first N calls, for a smoke test")
    ap.add_argument("--check-done", action="store_true", help="exit 0 if nothing is left to run, 1 otherwise")
    ap.add_argument("--part", type=int, help="run only this part (1..--parts), into its own file")
    ap.add_argument("--parts", type=int, help="number of parts the prompts are split into")
    args = ap.parse_args()
    if (args.part is None) != (args.parts is None):
        raise SystemExit("--part and --parts go together")
    if args.parts is not None and not 1 <= args.part <= args.parts:
        raise SystemExit(f"--part must be between 1 and {args.parts}")

    model = load_model(args.model)
    settings = load_settings()

    sampling = {"temperature": float(settings["temperature"]), "top_p": float(settings["top_p"]),
                "top_k": int(settings["top_k"])}
    if args.judge:
        prompts_file = RESULTS / "processed" / "judge_prompts.csv"
        files = answer_files(args.model, "judge")
        out = files[0] if args.parts is None else RESULTS / "raw" / "judge" / f"{args.model}.part{args.part}of{args.parts}.jsonl"
        sampling["temperature"] = float(settings["judge_temperature"])
        max_tokens, repeats = int(settings["judge_max_tokens"]), 1
    else:
        prompts_file = REPO / "experiment" / "prompts" / "prompts.csv"
        name = args.model if args.tag == "main" else f"{args.model}__{args.tag}"
        files = answer_files(name)
        out = files[0] if args.parts is None else RESULTS / "raw" / f"{name}.part{args.part}of{args.parts}.jsonl"
        max_tokens = int(settings["max_tokens_think" if "think" in args.model else "max_tokens"])
        repeats = args.repeats
        for key, value in (("temperature", args.temperature), ("top_p", args.top_p), ("top_k", args.top_k)):
            if value is not None:
                sampling[key] = value
        if sampling["temperature"] == 0 and repeats != 1:
            raise SystemExit("temperature 0 gives the same answer every time: add --repeats 1")

    prompts = [p for p in iter_csv(prompts_file)
               if (not args.variant or p["variant"] == args.variant)
               and (args.parts is None or in_part(p["prompt_id"], args.part, args.parts))]
    todo = pending(prompts, done_keys(files), repeats)[: args.limit]
    if args.check_done:
        part = f", part {args.part} of {args.parts}" if args.parts is not None else ""
        print(f"{len(todo)} calls left for {args.model} ({args.tag}{part})")
        sys.exit(0 if not todo else 1)

    base_url = os.environ["BASE_URL"]
    served_name = os.environ.get("MODEL_NAME", model["model_id"])
    weights = check_server(base_url, served_name, model, max_tokens)
    print(f"{len(todo)} calls to {args.model} (weights {weights})")
    extra = json.loads(model["extra_body"]) if model["extra_body"] else {}
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    stop = threading.Event()
    errors_in_a_row = [0]

    def run(item):
        if stop.is_set():
            return
        prompt, repeat = item
        body = {
            "model": served_name,
            "messages": ([{"role": "system", "content": prompt["system"]}] if prompt["system"] else [])
                        + [{"role": "user", "content": prompt["user"]}],
            **sampling,
            "max_tokens": max_tokens,
            "seed": int(settings["seed"]) + repeat,
            **extra,
        }
        try:
            text, finish, prompt_tokens, answer_tokens = call(base_url, body)
            error = ""
        except Exception as e:
            text, finish, prompt_tokens, answer_tokens, error = "", "", None, None, str(e) or type(e).__name__
        record = {"prompt_id": prompt["prompt_id"], "prompt_hash": prompt["prompt_hash"], "repeat": repeat,
                  "model": args.model, "run": args.tag, "weights": weights, "revision": model.get("revision", ""),
                  **sampling, "max_tokens": max_tokens, "text": text, "finish_reason": finish,
                  "prompt_tokens": prompt_tokens, "answer_tokens": answer_tokens, "error": error}
        with lock:
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            errors_in_a_row[0] = errors_in_a_row[0] + 1 if error else 0
            if errors_in_a_row[0] >= MAX_ERRORS_IN_A_ROW:
                stop.set()

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(run, todo))
    if stop.is_set():
        raise SystemExit(f"stopped after {MAX_ERRORS_IN_A_ROW} errors in a row; last answers in {out}")
    print(f"done, answers in {out}")


if __name__ == "__main__":
    main()
