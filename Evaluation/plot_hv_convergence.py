from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Plot hypervolume convergence curves for each algorithm.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "Data"
        / "EvalOutput"
        / "hv_convergence.csv",
        help="Path to the hv_convergence.csv file (defaults to the repository copy).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional path to save the generated figure. If omitted, the plot is "
            "saved as 'hv_convergence_plot.png' next to the CSV file."
        ),
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot window in addition to saving the figure.",
    )
    return parser.parse_args()


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load the convergence data from the provided CSV file."""

    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Could not find hv_convergence data at '{csv_path}'."
        )
    return pd.read_csv(csv_path)


def create_plot(df: pd.DataFrame) -> plt.Figure:
    """Create the convergence plot figure."""

    if df.empty:
        raise ValueError("The convergence data is empty. Nothing to plot.")

    algorithms = df["Algorithm"].unique()
    fig, ax = plt.subplots(figsize=(10, 6))

    for algorithm in algorithms:
        subset = df[df["Algorithm"] == algorithm].sort_values("Generation")
        generations = subset["Generation"].to_numpy()
        median = subset["median"].to_numpy()
        q1 = subset["q1"].to_numpy()
        q3 = subset["q3"].to_numpy()

        ax.plot(generations, median, label=algorithm)
        ax.fill_between(generations, q1, q3, alpha=0.0)

    # ax.set_title("Hypervolume Convergence by Algorithm")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Hypervolume")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    # ax.legend(loc="upper left")

    fig.tight_layout()
    return fig


def main() -> None:
    args = parse_args()
    df = load_data(args.csv)
    fig = create_plot(df)

    output_path = args.output
    if output_path is None:
        output_path = args.csv.with_name("hv_convergence_plot.png")

    fig.savefig(output_path, dpi=300)
    print(f"Saved convergence plot to {output_path}")

    if args.show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
