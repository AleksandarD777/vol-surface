import pandas as pd
import numpy as np
from scipy.stats import norm

from vol_surface.deribit import get_book_summary_by_currency, get_instruments
from vol_surface.market_data import (
    filter_illiquid_options,
    merge_market_data,
    prepare_surface_data,
)

"""Black Scholes function, which needs the following parameters: (s,k,T,sigma,r)
    s: underlying price
    k: strike
    T: time to maturity
    sigma: implied volatility
    r: risk-free rate
    
    The function aims to compute the price of the option"""


""" nel main io voglio che mi stampi un dataframe che sia price,s,k,T,sigma,r
"""

RISK_FREE_RATE = 0.0  # underlying_price is the forward of each expiry, so r = 0


def add_black_scholes_price(
    df: pd.DataFrame, r: float = RISK_FREE_RATE
) -> pd.DataFrame:
    """Add a 'bs_price' column , using Deribit's mark iv as sigma."""
    df = df.copy()

    prices = []  # empty list, one price per option will be added

    for i in range(len(df)):
        # take the values of row number i
        s = df["underlying_price"].iloc[i]
        k = df["strike"].iloc[i]
        sigma = df["mark_iv"].iloc[i] / 100
        t = df["time_to_maturity"].iloc[i]
        option_type = df["option_type"].iloc[i]

        price = black_scholes_price(s, k, r, sigma, t, option_type)
        prices.append(price)  # add the price at the end of the list

    df["bs_price"] = prices  # the list becomes a new column
    return df


def get_d1_d2(
    s: float, k: float, r: float, sigma: float, T: float
) -> tuple[float, float]:
    """Return d1 and d2 of the Black-Scholes formula."""
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2


def black_scholes_price(
    s: float, k: float, r: float, sigma: float, T: float, option_type: str
) -> float:
    """Return the Black-Scholes price of an option call or put.

    With s = forward of the expiry and r = 0 this is Black-76 model (used for Deribit).
    """
    d1, d2 = get_d1_d2(s, k, r, sigma, T)

    if option_type == "call":
        return s * norm.cdf(d1) - k * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        return k * np.exp(-r * T) * norm.cdf(-d2) - s * norm.cdf(-d1)
    raise ValueError(f"option_type must be 'call' or 'put', got {option_type!r}")


if __name__ == "__main__":
    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    df = merge_market_data(instruments, book_summary_by_currency)
    df = prepare_surface_data(df)
    df = filter_illiquid_options(df, min_days=7)

    df = add_black_scholes_price(df)

    # check: BS price with Deribit's IV vs market mid price (BTC -> USD)
    df["market_price"] = (
        (df["bid_price"] + df["ask_price"]) / 2 * df["underlying_price"]
    )
    print(
        df[
            [
                "strike",
                "option_type",
                "time_to_maturity",
                "mark_iv",
                "bs_price",
                "market_price",
            ]
        ]
    )
