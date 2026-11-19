import pytest

from pipeline.prompt_builder.build_prompts import build, split_prompt

BAR = "=" * 72
PROMPT_FILE = f"""VARIANT: base
header line
{BAR}
SYSTEM PROMPT
{BAR}
You are a case assistant.
{BAR}
USER MESSAGE, WORDING 1 OF 2
{BAR}
Assess this: {{application}}
Answer as JSON: {{"visa_score": 0-100}}
{BAR}
USER MESSAGE, WORDING 2 OF 2
{BAR}
APPLICATION
{{application}}
"""
APPLICATION = "Name: {{applicant.name}}\nNationality: {{nationality.demonym}}\nTravel document: {{nationality.demonym}} passport"
APPLICANTS = [{"applicant_id": "a1", "name": "Sam"}, {"applicant_id": "a2", "name": "Kim"}]
NATIONALITIES = [{"country": "Syria", "demonym": "Syrian"}, {"country": "Qatar", "demonym": "Qatari"}]


def prompts(wordings=(1, 2)):
    system, users = split_prompt(PROMPT_FILE)
    return {("base", w): {"system": system, "user": users[w], "output": "score", "repeats": 5} for w in wordings}


def test_file_is_split_and_every_combination_built_once():
    rows = build(prompts(), APPLICATION, APPLICANTS, NATIONALITIES)
    assert len({r["prompt_id"] for r in rows}) == 2 * 2 * 2
    first = rows[0]
    assert first["system"] == "You are a case assistant."
    assert first["user"] == ('Assess this: Name: Sam\nNationality: Syrian\nTravel document: Syrian passport\n'
                             'Answer as JSON: {"visa_score": 0-100}')


def test_prompts_differ_only_in_the_nationality_and_hash_follows_the_text():
    syria, qatar = build(prompts((1,)), APPLICATION, APPLICANTS[:1], NATIONALITIES)
    assert syria["user"].replace("Syrian", "X") == qatar["user"].replace("Qatari", "X")
    assert syria["prompt_hash"] != qatar["prompt_hash"]


def test_misspelt_blank_fails():
    with pytest.raises(ValueError):
        build(prompts(), APPLICATION + "{{nationalty.demonym}}", APPLICANTS, NATIONALITIES)
