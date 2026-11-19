from pipeline.judge.build_judge_prompts import mask
from pipeline.judge.parse_judge import CODES, parse


def test_nationality_is_hidden_but_residence_is_kept():
    text = "Nationality: Syrian. Born in Syria, lives in the United Arab Emirates."
    assert mask(text, {"demonym": "Syrian", "country": "Syria"}) == (
        "Nationality: [NATIONALITY]. Born in [PASSPORT COUNTRY], lives in the United Arab Emirates.")
    assert "United Arab Emirates" in mask(text, {"demonym": "Emirati", "country": "United Arab Emirates"})


def test_codes_are_read_and_incomplete_answers_rejected():
    answer = "{" + ", ".join(f'"{c}": "no"' for c in CODES) + ', "evidence": ""}'
    assert parse(answer)["funds_ok"] == 0
    assert parse(answer.replace('"funds_ok": "no", ', "")) is None
