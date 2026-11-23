"""Nationality effects and their tests. The notebooks in this folder import from here."""
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results"
CELL = ["model", "run", "variant", "wording", "applicant_id", "repeat"]
WEALTH_RANK = {"poor": 1, "normal": 2, "rich": 3}


def load_answers():
    answers = pd.read_csv(RESULTS / "processed" / "answers.csv")
    nationalities = pd.read_csv(REPO / "experiment" / "countries" / "nationalities.csv")
    applicants = pd.read_csv(REPO / "experiment" / "applicants" / "applicants.csv")
    return (answers.merge(nationalities, on="country", how="left")
                   .merge(applicants, on="applicant_id", how="left"))


def load_judge_codes():
    main = load_answers().query("run == 'main'")
    return main.merge(pd.read_csv(RESULTS / "processed" / "judge_codes.csv"), on=["model", "prompt_id", "repeat"])


def main_run(df):
    return df[df["run"] == "main"]


def readable(df):
    return df[df["status"] == "ok"].copy()


def main_comparison(df):
    return df[(df["group"] == "arab") & (df["visa_required"] == "yes")]


def deviations(df, outcome="visa_score"):
    """outcome: visa_score (0-100) or granted (1 = grant, 0 = refuse, for the binary variant)."""
    df = df.copy()
    df["deviation"] = df[outcome] - df.groupby(CELL)[outcome].transform("mean")
    return df


def effects(df, by=("model",), outcome="visa_score"):
    return deviations(df, outcome).groupby([*by, "country"])["deviation"].mean()


def gap(country_effects):
    return country_effects.max() - country_effects.min()


def permutation_p(df, statistic, n=5000, seed=617, outcome="visa_score"):
    """One model. p = share of label shuffles within cells whose statistic is at least the observed one."""
    rng = np.random.default_rng(seed)
    df = deviations(df, outcome).sort_values(CELL).reset_index(drop=True)
    observed = statistic(df)
    cells = df.groupby(CELL, sort=False).ngroup().to_numpy()
    countries = df["country"].to_numpy()
    hits = 0
    for _ in range(n):
        order = np.lexsort((rng.random(len(df)), cells))
        hits += statistic(df.assign(country=countries[order])) >= observed
    return observed, (hits + 1) / (n + 1)


def spread(df):
    return df.groupby("country")["deviation"].mean().std()


def country_wealth():
    nationalities = pd.read_csv(REPO / "experiment" / "countries" / "nationalities.csv")
    return nationalities.set_index("country")["wealth_group"].map(WEALTH_RANK)


WEALTH = country_wealth()


def wealth_rho(df):
    """Spearman correlation of the country effects with the wealth order (poor, normal, rich).
    The wealth comes from nationalities.csv by country name, never from the rows: permutation_p shuffles
    only the country labels, so a wealth column on the rows would no longer belong to the country."""
    effect = df.groupby("country")["deviation"].mean()
    return effect.rank().corr(WEALTH.reindex(effect.index).rank())
