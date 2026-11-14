"""Implied volatility inversion from option prices (Black-Scholes)."""

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from vol_surface.deribit import get_book_summary_by_currency, get_instruments
from vol_surface.market_data import (
    filter_illiquid_options,
    merge_market_data,
    prepare_surface_data,
)

VOL_LOW = 1e-4
VOL_HIGH = 5.0


def bs_price(
    S: float, K: float, r: float, sigma: float, T: float, option_type: str = "call"
) -> float:
    """Black-Scholes price of a European option.

    S is the underlying price (for Deribit, the forward), K the strike,
    r the risk-free rate, sigma the volatility and T the time to maturity in years.
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    discount = np.exp(-r * T)

    if option_type == "call":
        return S * norm.cdf(d1) - K * discount * norm.cdf(d2)
    if option_type == "put":
        return K * discount * norm.cdf(-d2) - S * norm.cdf(-d1)
    raise ValueError(f"option_type must be 'call' or 'put', got {option_type!r}")


def implied_vol(
    S: float, K: float, r: float, T: float, price: float, option_type: str = "call"
) -> float:
    """Implied volatility of a European option, found with Brent's method.

    Returns nan if the price is outside the no-arbitrage bounds or if no
    volatility between VOL_LOW and VOL_HIGH matches it.
    """
    discounted_strike = K * np.exp(-r * T)
    if option_type == "call":
        lower, upper = max(S - discounted_strike, 0.0), S
    elif option_type == "put":
        lower, upper = max(discounted_strike - S, 0.0), discounted_strike
    else:
        raise ValueError(f"option_type must be 'call' or 'put', got {option_type!r}")

    if not lower < price < upper:
        return np.nan

    def price_gap(sigma: float) -> float:
        return bs_price(S, K, r, sigma, T, option_type) - price

    if price_gap(VOL_LOW) * price_gap(VOL_HIGH) > 0:
        return np.nan
    return brentq(price_gap, VOL_LOW, VOL_HIGH)


def add_implied_vol(df: pd.DataFrame, r: float = 0.0) -> pd.DataFrame:
    """Add the implied volatility computed from the bid/ask mid price.

    Deribit quotes prices in BTC, so the mid price is converted to USD
    by multiplying it by the underlying price. Rows without a valid bid
    and ask (zero or missing) get nan.
    """
    df = df.copy()
    valid = (df["bid_price"] > 0) & (df["ask_price"] > 0)
    mid_btc = ((df["bid_price"] + df["ask_price"]) / 2).where(valid)
    df["mid_price_usd"] = mid_btc * df["underlying_price"]

    df["implied_vol"] = [
        implied_vol(S, K, r, T, price, option_type)
        for S, K, T, price, option_type in zip(
            df["underlying_price"],
            df["strike"],
            df["time_to_maturity"],
            df["mid_price_usd"],
            df["option_type"],
        )
    ]
    return df


if __name__ == "__main__":
    instruments = get_instruments(currency="BTC", kind="option")
    book_summary = get_book_summary_by_currency(currency="BTC", kind="option")

    df = merge_market_data(instruments, book_summary)
    df = prepare_surface_data(df)
    df = filter_illiquid_options(df)
    df = add_implied_vol(df)

    df["mark_iv_decimal"] = df["mark_iv"] / 100
    df["diff"] = df["implied_vol"] - df["mark_iv_decimal"]

    print("Options:", len(df), "- not invertible:", df["implied_vol"].isna().sum())
    print(df[["instrument_name", "implied_vol", "mark_iv_decimal", "diff"]].head(10))
    print(df["diff"].describe())