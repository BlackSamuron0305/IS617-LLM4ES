"""Look of the figures: the colours and fonts of the pitch deck (navy 14213D, gold E0A526, blues 2D4A86 / 6C8CC0 /
C9D7EC, grey text 5C677D, red C1121F), as in the midterm. Every figure is saved to results/figures/; the ones the final
deck and the report use (deck=True) are also copied to report/3_final_presentation/figures/ and
report/4_final_report/figures/results/."""
import shutil

import matplotlib.pyplot as plt

from pipeline.analysis.stats import REPO, RESULTS

NAVY, GOLD, BLUE, LIGHT_BLUE, ICE, GREY, RED = "#14213D", "#E0A526", "#2D4A86", "#6C8CC0", "#C9D7EC", "#5C677D", "#C1121F"
WEALTH = {"rich": GOLD, "normal": LIGHT_BLUE, "poor": BLUE}
MAIN = ["gemma-4-31b-it", "mistral-small-3.2-24b-instruct", "qwen3-32b"]
MAIN_COLOURS = dict(zip(MAIN, (NAVY, LIGHT_BLUE, GOLD)))
LADDER = ["qwen3-0.6b", "qwen3-1.7b", "qwen3-4b", "qwen3-8b", "qwen3-14b", "qwen3-32b"]
ORDER = MAIN + LADDER[:-1] + ["qwen3-32b-think"]
LABEL = {"gemma-4-31b-it": "Gemma 4 31B", "mistral-small-3.2-24b-instruct": "Mistral Small 3.2 24B",
         "qwen3-32b": "Qwen3 32B", "qwen3-0.6b": "Qwen3 0.6B", "qwen3-1.7b": "Qwen3 1.7B", "qwen3-4b": "Qwen3 4B",
         "qwen3-8b": "Qwen3 8B", "qwen3-14b": "Qwen3 14B", "qwen3-32b-think": "Qwen3 32B thinking"}
FIGURES = RESULTS / "figures"
DECK = REPO / "report" / "3_final_presentation" / "figures"
PAPER = REPO / "report" / "4_final_report" / "figures" / "results"


def use():
    plt.rcParams.update({
        "axes.spines.top": False, "axes.spines.right": False, "font.family": ["Calibri", "DejaVu Sans"],
        "font.size": 12, "text.color": NAVY, "axes.labelcolor": NAVY, "axes.edgecolor": ICE, "xtick.color": GREY,
        "ytick.color": GREY, "axes.titleweight": "bold", "axes.titlesize": 14, "axes.labelsize": 11,
        "legend.fontsize": 11, "legend.frameon": False, "figure.dpi": 100})


def save(fig, name, deck=False):
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    if deck:
        for folder in (DECK, PAPER):
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, folder / name)
    return path
