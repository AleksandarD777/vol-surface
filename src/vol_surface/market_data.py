from datetime import UTC, datetime

import numpy as np
import pandas as pd

from vol_surface.deribit import get_book_summary_by_currency, get_instruments


def merge_market_data(
    instruments: list[dict], book_summary_by_currency: list[dict]
) -> pd.DataFrame:
    """Join instruments with their book summaries, keeping only instruments present in both."""

    instruments_columns = [
        "instrument_name",
        "expiration_timestamp",
        "strike",
        "option_type",
    ]
    book_summary_columns = [
        "instrument_name",
        "mark_iv",
        "underlying_price",
        "bid_price",
        "ask_price",
    ]

    df_inst = pd.DataFrame(instruments)[instruments_columns]
    df_book = pd.DataFrame(book_summary_by_currency)[book_summary_columns]
    df = pd.merge(df_inst, df_book, how="inner", on="instrument_name")
    return df


def prepare_surface_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for surface plotting function.

    Compute moneyness and time to maturity and Deletes ITM options.
    """
    df = df.copy()
    df["moneyness"] = np.log(df["strike"] / df["underlying_price"])

    expiry_dt = pd.to_datetime(df["expiration_timestamp"], unit="ms", utc=True)
    current_dt = datetime.now(UTC)
    df["time_to_maturity"] = (expiry_dt - current_dt) / pd.Timedelta(days=365)

    filtered_df = df[
        ((df["option_type"] == "call") & (df["moneyness"] >= 0))
        | ((df["option_type"] == "put") & (df["moneyness"] <= 0))
    ]

    return filtered_df


def filter_illiquid_options(df: pd.DataFrame, min_days: int = 7) -> pd.DataFrame:
    """Remove options close to expiration and that don't have both a bid and an ask"""

    df = df[df["time_to_maturity"] >= (min_days / 365)]
    df = df[df["bid_price"].notna() & df["ask_price"].notna()]

    return df


def select_surface_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return the 3 columns needed to plot the surface"""

    return df[["moneyness", "time_to_maturity", "mark_iv"]]


def run_surface_data_pipeline(
    instruments: list[dict],
    book_summary_by_currency: list[dict],
    filter_illiquid: bool = True,
    min_days: int = 7,
) -> pd.DataFrame:
    """Run full market data pipeline"""

    df = merge_market_data(instruments, book_summary_by_currency)
    print("questo e' il df:")
    print(df)
    plotting_data = prepare_surface_data(df=df)
    if filter_illiquid:
        plotting_data = filter_illiquid_options(plotting_data, min_days=min_days)
    plotting_data = select_surface_columns(plotting_data)

    return plotting_data


if __name__ == "__main__":
    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    plotting_data = run_surface_data_pipeline(
        instruments, book_summary_by_currency, filter_illiquid=True, min_days=7
    )
    print(plotting_data.describe())
