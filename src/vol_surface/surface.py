import matplotlib.pyplot as plt
import pandas as pd
from vol_surface.market_data import run_surface_data_pipeline
from vol_surface.deribit import get_instruments, get_book_summary_by_currency


def plot_surface(df: pd.DataFrame) -> plt.Figure:
    """Create a 3D scatter plot of the raw IV points."""
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.scatter(xs=df["moneyness"], ys=df["time_to_maturity"], zs=df["mark_iv"])
    ax.set_xlabel("Log-moneyness ln(K/F)")
    ax.set_ylabel("Time to maturity (years)")
    ax.set_zlabel("Implied Volatility (%)")

    return fig


if __name__ == "__main__":
    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    plotting_data = run_surface_data_pipeline(
        instruments, book_summary_by_currency, filter_illiquid=True, min_days=15
    )

    fig = plot_surface(plotting_data)
    fig.savefig("figures/surface.png")
