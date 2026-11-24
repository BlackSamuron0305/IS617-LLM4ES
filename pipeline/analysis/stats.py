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


def points(df):
    """Adds a column 'points': the visa score, or for the yes/no variant 100 x granted, so that a nationality's
    effect there is its difference in the share of grants, in percentage points. Use with outcome="points"."""
    df = df.copy()
    df["points"] = df["visa_score"].fillna(100 * df["granted"])
    return df


def complete_models(df):
    """Models whose main run has every call. Pass the answers before readable(), so a model with a few unreadable
    answers still counts as complete. A run still in progress (thinking) covers a scattered sample of the prompts,
    so few nationalities share a cell; report it apart, never next to the complete ones."""
    calls = df[df["run"] == "main"].groupby("model").size()
    return sorted(calls[calls == calls.max()].index)


def holm(p_values):
    """Holm correction. p_values: a pandas Series; returns the adjusted values in the same order."""
    order = p_values.sort_values()
    m = len(order)
    adjusted = (order * np.arange(m, 0, -1)).cummax().clip(upper=1)
    return adjusted.reindex(p_values.index)


def _spread_arrays(scores, cells, countries, n_countries):
    cell_mean = np.bincount(cells, scores) / np.bincount(cells)
    dev = scores - cell_mean[cells]
    effect = np.bincount(countries, dev, minlength=n_countries) / np.bincount(countries, minlength=n_countries)
    return effect.std(ddof=1)


def paired_change_p(a, b, n=2000, seed=617, outcome="visa_score"):
    """One model, two prompt versions a and b of the same calls (applicant, nationality, repetition).
    Statistic: spread under a minus spread under b. Test: swap a and b at random within each pair of calls.
    Returns the observed change and the two-sided p."""
    key = ["applicant_id", "country", "repeat"]
    pairs = a[key + [outcome]].merge(b[key + [outcome]], on=key, suffixes=("_a", "_b"))
    cells = pairs.groupby(["applicant_id", "repeat"]).ngroup().to_numpy()
    countries = pairs["country"].astype("category").cat.codes.to_numpy()
    k = countries.max() + 1
    xa, xb = pairs[f"{outcome}_a"].to_numpy(float), pairs[f"{outcome}_b"].to_numpy(float)

    def change(sa, sb):
        return _spread_arrays(sa, cells, countries, k) - _spread_arrays(sb, cells, countries, k)

    observed = change(xa, xb)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n):
        swap = rng.random(len(xa)) < 0.5
        hits += abs(change(np.where(swap, xb, xa), np.where(swap, xa, xb))) >= abs(observed)
    return observed, (hits + 1) / (n + 1)


def funds_step(df):
    """Score jump at the money threshold: edge_funds_just_above (EUR 571 for EUR 560 needed) minus
    edge_funds_just_below (EUR 523), and that jump per euro. Two applicants who differ mainly in their savings,
    so this is an illustration, not a price."""
    means = df.groupby("applicant_id")["visa_score"].mean()
    above, below = "edge_funds_just_above", "edge_funds_just_below"
    euros = df.drop_duplicates("applicant_id").set_index("applicant_id")["savings_eur"]
    euros = euros.astype(str).str.replace(",", "").astype(float)
    step = means[above] - means[below]
    return step, step / (euros[above] - euros[below])


def chance_gap(df, n=200, seed=617, outcome="visa_score"):
    """One model. The gap (highest minus lowest nationality) to expect from chance alone: the mean gap after
    shuffling the nationality labels within each cell. With few answers per nationality, as for a yes/no decision,
    the observed gap is large by chance too; the part above this value is what the passport adds."""
    rng = np.random.default_rng(seed)
    df = deviations(df, outcome).sort_values(CELL).reset_index(drop=True)
    cells = df.groupby(CELL, sort=False).ngroup().to_numpy()
    countries = df["country"].to_numpy()
    gaps = []
    for _ in range(n):
        order = np.lexsort((rng.random(len(df)), cells))
        effect = df.assign(country=countries[order]).groupby("country")["deviation"].mean()
        gaps.append(effect.max() - effect.min())
    return float(np.mean(gaps))


def resample_applicants(per_applicant, statistic, n=2000, seed=617):
    """Bootstrap over applicants: per_applicant has one row per applicant; statistic maps a resampled frame to a
    number. Returns the n resampled values. The 40 applicants are the unit that was sampled (by us); answers to the
    same application are not independent of each other."""
    rng = np.random.default_rng(seed)
    rows = len(per_applicant)
    return np.array([statistic(per_applicant.iloc[rng.integers(0, rows, rows)]) for _ in range(n)])


def bootstrap_effects(df, statistic, n=2000, seed=617, outcome="visa_score"):
    """One model. Bootstrap over applicants of a statistic of the nationality effects (gap, spread, wealth_order...).
    Deviations are taken once on all data: a cell lies inside one applicant, so resampling applicants keeps every
    cell whole. Returns the n resampled values."""
    d = deviations(df, outcome)
    grouped = d.groupby(["applicant_id", "country"])["deviation"]
    total = grouped.sum().unstack(fill_value=0)
    count = grouped.count().unstack(fill_value=0).reindex(index=total.index, columns=total.columns)
    countries = total.columns
    total, count = total.to_numpy(), count.to_numpy()
    rng = np.random.default_rng(seed)
    rows = total.shape[0]
    values = []
    for _ in range(n):
        idx = rng.integers(0, rows, rows)
        with np.errstate(invalid="ignore", divide="ignore"):
            effect = pd.Series(total[idx].sum(0) / count[idx].sum(0), index=countries)
        values.append(statistic(effect.dropna()))
    return np.array(values)


def interval(values, level=0.95):
    """Percentile interval of bootstrap values: (low, high)."""
    tail = (1 - level) / 2 * 100
    return float(np.nanpercentile(values, tail)), float(np.nanpercentile(values, 100 - tail))


def effect_gap(effect):
    return effect.max() - effect.min()


def effect_spread(effect):
    return effect.std()


def wealth_order(effect):
    """Spearman correlation of country effects with the wealth rank (poor, normal, rich)."""
    return effect.rank().corr(WEALTH.reindex(effect.index).rank())
