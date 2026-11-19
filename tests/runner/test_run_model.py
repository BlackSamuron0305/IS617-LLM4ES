from pipeline.runner.run_model import pending


def test_only_missing_or_changed_prompts_run():
    prompts = [{"prompt_id": "a", "prompt_hash": "new", "repeats": "2"},
               {"prompt_id": "b", "prompt_hash": "same", "repeats": "2"}]
    done = {("a", 1, "old"), ("a", 2, "old"), ("b", 1, "same"), ("b", 2, "same")}
    assert [(p["prompt_id"], k) for p, k in pending(prompts, done)] == [("a", 1), ("a", 2)]


def test_parts_cover_every_prompt_exactly_once():
    from pipeline.runner.run_model import in_part
    ids = [f"p{i}" for i in range(2000)]
    parts = 7
    owners = [[k for k in range(1, parts + 1) if in_part(i, k, parts)] for i in ids]
    assert all(len(o) == 1 for o in owners)
    sizes = [sum(o == [k] for o in owners) for k in range(1, parts + 1)]
    assert min(sizes) > 2000 / parts * 0.8


def test_answers_in_main_and_part_files_count_as_done(tmp_path, monkeypatch):
    import json
    from pipeline.runner import run_model
    raw = tmp_path / "raw"
    raw.mkdir()
    def write(name, prompt_id, error=""):
        with open(raw / name, "a", encoding="utf-8") as f:
            f.write(json.dumps({"prompt_id": prompt_id, "repeat": 1, "prompt_hash": "h", "error": error}) + "\n")
    write("m.jsonl", "a")
    write("m.part1of2.jsonl", "b")
    write("m.part2of2.jsonl", "c", error="timeout")
    write("m-think.part1of2.jsonl", "d")
    write("m__t0.jsonl", "e")
    monkeypatch.setattr(run_model, "RESULTS", tmp_path)
    assert run_model.done_keys(run_model.answer_files("m")) == {("a", 1, "h"), ("b", 1, "h")}
