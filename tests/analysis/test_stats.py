import pandas as pd

from pipeline.analysis.stats import deviations, effects, permutation_p, spread, wealth_rho


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


def test_wealth_rho_takes_the_wealth_from_the_country_not_from_the_row():
    # Syria poor, Jordan normal, Qatar rich. The permutation test shuffles only the country labels,
    # so a wealth_group column left on the rows no longer belongs to the country: it must be ignored.
    df = deviations(answers(syria_penalty=6))
    df["visa_score"] += df["country"].map({"Qatar": 3, "Jordan": 0, "Syria": 0})
    df = deviations(df)
    df["wealth_group"] = "normal"
    assert round(wealth_rho(df), 6) == 1
    p = permutation_p(df.drop(columns="deviation"), wealth_rho, n=200)[1]
    assert p > 0.05  # three countries: a perfect order happens by chance one time in six


def test_points_turns_grants_into_percentage_points():
    from pipeline.analysis.stats import points
    df = pd.DataFrame({"visa_score": [70.0, None, None], "granted": [None, 1.0, 0.0]})
    assert points(df)["points"].tolist() == [70, 100, 0]


def test_holm_keeps_order_and_caps_at_one():
    from pipeline.analysis.stats import holm
    p = pd.Series({"a": 0.04, "b": 0.01, "c": 0.5})
    assert holm(p).round(6).to_dict() == {"a": 0.08, "b": 0.03, "c": 0.5}


def test_paired_change_finds_a_gap_that_one_version_removes():
    from pipeline.analysis.stats import paired_change_p
    with_gap, without = answers(syria_penalty=6), answers(syria_penalty=0)
    change, p = paired_change_p(with_gap, without, n=200)
    assert change > 0 and p < 0.05
    assert paired_change_p(with_gap, with_gap, n=200)[1] > 0.5


def test_chance_gap_is_below_a_planted_gap_and_near_a_missing_one():
    from pipeline.analysis.stats import chance_gap, gap
    planted = answers(syria_penalty=6)
    assert chance_gap(planted, n=100) < gap(effects(planted))
    assert chance_gap(answers(0), n=100) == 0  # all deviations equal in every cell: no gap, shuffled or not


def test_bootstrap_interval_covers_a_planted_gap_and_reaches_zero_without_one():
    from pipeline.analysis.stats import bootstrap_effects, effect_gap, interval
    low, high = interval(bootstrap_effects(answers(syria_penalty=6), effect_gap, n=200))
    assert low <= 6 <= high + 1e-9
    assert interval(bootstrap_effects(answers(0), effect_gap, n=200)) == (0.0, 0.0)


def test_complete_models_counts_calls_not_readable_answers():
    from pipeline.analysis.stats import complete_models
    df = pd.DataFrame({"model": ["a"] * 4 + ["b"] * 4 + ["c"] * 2, "run": "main",
                       "status": ["ok"] * 3 + ["unreadable"] + ["ok"] * 6})
    assert complete_models(df) == ["a", "b"]


def test_funds_step_is_the_jump_between_the_two_threshold_applicants():
    from pipeline.analysis.stats import funds_step
    df = pd.DataFrame({"applicant_id": ["edge_funds_just_below", "edge_funds_just_above"] * 2,
                       "visa_score": [30, 80, 40, 90], "savings_eur": ["523", "571"] * 2})
    step, per_euro = funds_step(df)
    assert step == 50 and round(per_euro, 4) == round(50 / 48, 4)
