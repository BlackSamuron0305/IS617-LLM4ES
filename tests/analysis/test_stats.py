import pandas as pd

from pipeline.analysis.stats import effects, permutation_p, spread


def answers(syria_penalty):
    rows = []
    for applicant, base in (("a1", 90), ("a2", 60)):
        for repeat in range(1, 6):
            for country in ("Syria", "Qatar", "Jordan"):
                score = base - (syria_penalty if country == "Syria" else 0) + repeat % 2
                rows.append({"model": "m", "run": "main", "variant": "base", "wording": 1, "applicant_id": applicant,
                             "repeat": repeat, "country": country, "visa_score": score})
    return pd.DataFrame(rows)


def test_effects_remove_the_applicant_level():
    e = effects(answers(syria_penalty=6))
    assert round(e[("m", "Syria")], 6) == -4 and round(e[("m", "Qatar")], 6) == 2


def test_permutation_finds_a_planted_gap_and_not_a_missing_one():
    assert permutation_p(answers(6), spread, n=200)[1] < 0.05
    assert permutation_p(answers(0), spread, n=200)[1] > 0.05
