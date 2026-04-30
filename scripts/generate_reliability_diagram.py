"""Generate a reliability diagram PNG from eval baseline and golden dataset.

Reads evals/baseline.json (rubric scores) and evals/golden_dataset.json
(50 test cases) to produce assets/screenshots/reliability-diagram.png.

No LLM or database required -- runs from static eval artifacts.

Usage:
    python3 scripts/generate_reliability_diagram.py
    python3 scripts/generate_reliability_diagram.py --output path/to/out.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


REPO_ROOT = Path(__file__).parent.parent
BASELINE_PATH = REPO_ROOT / "evals" / "baseline.json"
DATASET_PATH = REPO_ROOT / "evals" / "golden_dataset.json"
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "screenshots" / "reliability-diagram.png"

# Brand palette matching EnterpriseHub README/dashboard screenshots
BRAND_BG = "#0D1117"
BRAND_SURFACE = "#161B22"
BRAND_BORDER = "#30363D"
BRAND_GREEN = "#46E3B7"
BRAND_BLUE = "#58A6FF"
BRAND_AMBER = "#E3B341"
BRAND_RED = "#F85149"
BRAND_TEXT = "#C9D1D9"
BRAND_MUTED = "#8B949E"


def _load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


def _category_counts(dataset: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tc in dataset:
        cat = tc.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _difficulty_counts(dataset: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tc in dataset:
        diff = tc.get("difficulty", "unknown")
        counts[diff] = counts.get(diff, 0) + 1
    return counts


def generate(output: Path = DEFAULT_OUTPUT) -> None:
    baseline = _load_json(BASELINE_PATH)
    dataset = _load_json(DATASET_PATH)

    rubrics: dict[str, float] = baseline.get("rubrics", {})
    generated_date: str = baseline.get("generated", "unknown")
    category_counts = _category_counts(dataset)
    difficulty_counts = _difficulty_counts(dataset)

    fig = plt.figure(figsize=(14, 8), facecolor=BRAND_BG)
    fig.suptitle(
        "EnterpriseHub — Eval Reliability Baseline",
        color=BRAND_TEXT,
        fontsize=15,
        fontweight="bold",
        y=0.97,
    )

    # Layout: 2 rows, 2 cols
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.35,
                          left=0.07, right=0.97, top=0.90, bottom=0.07)
    ax_rubric = fig.add_subplot(gs[0, :])   # rubric scores, full width
    ax_cat = fig.add_subplot(gs[1, 0])      # category distribution
    ax_diff = fig.add_subplot(gs[1, 1])     # difficulty distribution

    # --- Rubric baseline bar chart ---
    rubric_names = [r.capitalize() for r in rubrics]
    rubric_vals = list(rubrics.values())
    bar_colors = [BRAND_GREEN if v >= 0.95 else BRAND_BLUE if v >= 0.85 else BRAND_AMBER for v in rubric_vals]

    x = np.arange(len(rubric_names))
    bars = ax_rubric.bar(x, rubric_vals, color=bar_colors, width=0.5, zorder=3)

    ax_rubric.set_facecolor(BRAND_SURFACE)
    ax_rubric.set_ylim(0, 1.12)
    ax_rubric.set_xticks(x)
    ax_rubric.set_xticklabels(rubric_names, color=BRAND_TEXT, fontsize=11)
    ax_rubric.tick_params(axis="y", colors=BRAND_MUTED, labelsize=9)
    ax_rubric.set_ylabel("Score", color=BRAND_MUTED, fontsize=10)
    ax_rubric.set_title(
        f"LLM-as-Judge Rubric Scores  ·  baseline {generated_date}",
        color=BRAND_MUTED, fontsize=10, pad=8,
    )
    ax_rubric.axhline(0.85, color=BRAND_AMBER, linewidth=1, linestyle="--", zorder=2, alpha=0.7)
    ax_rubric.text(len(rubric_names) - 0.45, 0.865, "CI gate (0.85)",
                   color=BRAND_AMBER, fontsize=8, va="bottom", ha="right")
    for spine in ax_rubric.spines.values():
        spine.set_edgecolor(BRAND_BORDER)
    ax_rubric.yaxis.grid(True, color=BRAND_BORDER, linewidth=0.5, zorder=0)
    ax_rubric.set_axisbelow(True)

    for bar, val in zip(bars, rubric_vals):
        ax_rubric.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.015,
            f"{val:.0%}",
            ha="center", va="bottom",
            color=BRAND_TEXT, fontsize=10, fontweight="bold",
        )

    # --- Category distribution ---
    cat_order = ["seller_qualification", "buyer_scheduling", "lead_intake", "edge_case", "compliance"]
    cat_labels = [c.replace("_", "\n") for c in cat_order]
    cat_vals = [category_counts.get(c, 0) for c in cat_order]

    ax_cat.bar(range(len(cat_order)), cat_vals, color=BRAND_BLUE, width=0.6, zorder=3)
    ax_cat.set_facecolor(BRAND_SURFACE)
    ax_cat.set_xticks(range(len(cat_order)))
    ax_cat.set_xticklabels(cat_labels, color=BRAND_TEXT, fontsize=8)
    ax_cat.tick_params(axis="y", colors=BRAND_MUTED, labelsize=9)
    ax_cat.set_ylabel("Test cases", color=BRAND_MUTED, fontsize=9)
    ax_cat.set_title(f"Coverage by category  (n={sum(cat_vals)})", color=BRAND_MUTED, fontsize=10, pad=6)
    for spine in ax_cat.spines.values():
        spine.set_edgecolor(BRAND_BORDER)
    ax_cat.yaxis.grid(True, color=BRAND_BORDER, linewidth=0.5, zorder=0)
    ax_cat.set_axisbelow(True)
    for i, v in enumerate(cat_vals):
        ax_cat.text(i, v + 0.1, str(v), ha="center", va="bottom", color=BRAND_TEXT, fontsize=9)

    # --- Difficulty distribution ---
    diff_order = ["easy", "medium", "hard"]
    diff_colors = [BRAND_GREEN, BRAND_AMBER, BRAND_RED]
    diff_vals = [difficulty_counts.get(d, 0) for d in diff_order]
    total_diff = sum(diff_vals)

    wedges, texts, autotexts = ax_diff.pie(
        diff_vals,
        labels=[f"{d.capitalize()}\n({v})" for d, v in zip(diff_order, diff_vals)],
        colors=diff_colors,
        autopct="%1.0f%%",
        startangle=140,
        textprops={"color": BRAND_TEXT, "fontsize": 9},
        wedgeprops={"edgecolor": BRAND_SURFACE, "linewidth": 2},
    )
    for at in autotexts:
        at.set_color(BRAND_BG)
        at.set_fontweight("bold")
    ax_diff.set_facecolor(BRAND_BG)
    ax_diff.set_title(f"Difficulty distribution  (n={total_diff})", color=BRAND_MUTED, fontsize=10, pad=6)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight", facecolor=BRAND_BG)
    plt.close(fig)
    print(f"Reliability diagram written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
