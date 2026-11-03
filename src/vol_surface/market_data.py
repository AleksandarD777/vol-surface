from datetime import datetime, timezone
import pandas as pd
import numpy as np
from vol_surface.deribit import get_book_summary_by_currency, get_instruments


def merge_market_data(
    instruments: list[dict], book_summary_by_currency: list[dict]
) -> pd.DataFrame:
    """Join instruments with their book summaries, keeping only instruments present in both."""

    insturments_columns = [
        "instrument_name",
        "expiration_timestamp",
        "strike",
        "option_type",
    ]
    book_summary_columns = ["instrument_name", "mark_iv", "underlying_price"]

    df_inst = pd.DataFrame(instruments)[insturments_columns]
    df_book = pd.DataFrame(book_summary_by_currency)[book_summary_columns]
    df = pd.merge(df_inst, df_book, how="inner", on="instrument_name")
    return df


def prepare_surface_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares data for surface plotting function.

    Compute moneyness and time to maturity and Deletes ITM options.
    """
    df = df.copy()
    df["moneyness"] = np.log(df["strike"] / df["underlying_price"])

    expiry_dt = pd.to_datetime(df["expiration_timestamp"], unit="ms", utc=True)
    current_dt = datetime.now(timezone.utc)
    df["time_to_maturity"] = (expiry_dt - current_dt) / pd.Timedelta(days=365)

    filtered_df = df[
        ((df["option_type"] == "call") & (df["moneyness"] >= 0))
        | ((df["option_type"] == "put") & (df["moneyness"] <= 0))
    ]

    return filtered_df[["moneyness", "time_to_maturity", "mark_iv"]]


if __name__ == "__main__":
    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    df = merge_market_data(instruments, book_summary_by_currency)
    plotting_data = prepare_surface_data(df=df)
    print(plotting_data.head())
