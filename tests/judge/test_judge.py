from pipeline.judge.build_judge_prompts import mask
from pipeline.judge.parse_judge import CODES, parse


def test_nationality_is_hidden_but_residence_is_kept():
    text = "Nationality: Syrian. Born in Syria, lives in the United Arab Emirates."
    assert mask(text, {"demonym": "Syrian", "country": "Syria"}) == (
        "Nationality: [NATIONALITY]. Born in [PASSPORT COUNTRY], lives in the United Arab Emirates.")
    assert "United Arab Emirates" in mask(text, {"demonym": "Emirati", "country": "United Arab Emirates"})


def test_identical_judge_prompts_share_one_call():
    from pipeline.judge.build_judge_prompts import share
    rows, links = share([("m__p1__1", "same"), ("m__p2__3", "same"), ("m__p1__2", "other")])
    assert len(rows) == 2 and len(links) == 3
    assert links[0]["judge_prompt_id"] == links[1]["judge_prompt_id"] != links[2]["judge_prompt_id"]
    assert share([("x__p9__1", "same")])[0][0]["prompt_id"] == rows[0]["prompt_id"]   # stable across runs


def test_judge_answers_in_part_files_count_as_done(tmp_path, monkeypatch):
    import json
    from pipeline.runner import run_model
    judge = tmp_path / "raw" / "judge"
    judge.mkdir(parents=True)
    for name, prompt_id in (("olmo.jsonl", "ja"), ("olmo.part2of4.jsonl", "jb")):
        (judge / name).write_text(json.dumps({"prompt_id": prompt_id, "repeat": 1, "prompt_hash": "h",
                                              "error": ""}) + "\n", encoding="utf-8")
    monkeypatch.setattr(run_model, "RESULTS", tmp_path)
    assert run_model.done_keys(run_model.answer_files("olmo", "judge")) == {("ja", 1, "h"), ("jb", 1, "h")}


def test_codes_are_read_and_incomplete_answers_rejected():
    answer = "{" + ", ".join(f'"{c}": "no"' for c in CODES) + ', "evidence": ""}'
    assert parse(answer)["funds_ok"] == 0
    assert parse(answer.replace('"funds_ok": "no", ', "")) is None
