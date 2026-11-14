import numpy as np
import pandas as pd
from scipy.optimize import brentq

from vol_surface.deribit import get_book_summary_by_currency, get_instruments

from vol_surface.black_scholes import (
    RISK_FREE_RATE,
    add_black_scholes_price,
    black_scholes_price,
)

from vol_surface.market_data import (
    filter_illiquid_options,
    merge_market_data,
    prepare_surface_data,
)

SIGMA_MIN = 0.001  # lowest volatility searched (0.1%)
SIGMA_MAX = 5.0  # highest volatility searched (500%)


def price_difference(
    sigma: float, price: float, s: float, k: float, r: float, T: float, option_type: str
) -> float:
    """Return the Black-Scholes price with this sigma minus the market price.

    The implied volatility is the sigma that makes this difference zero.
    """
    return black_scholes_price(s, k, r, sigma, T, option_type) - price


def implied_volatility(
    price: float, s: float, k: float, r: float, T: float, option_type: str
) -> float:
    """Return the implied volatility (decimal, 0.45 = 45%) of one option.

    Returns NaN when no sigma between SIGMA_MIN and SIGMA_MAX gives back the price.
    """
    arguments = (price, s, k, r, T, option_type)

    # brentq needs the difference to change sign between SIGMA_MIN and SIGMA_MAX
    difference_at_min = price_difference(SIGMA_MIN, *arguments)
    difference_at_max = price_difference(SIGMA_MAX, *arguments)
    if difference_at_min * difference_at_max > 0:
        return np.nan

    return brentq(price_difference, SIGMA_MIN, SIGMA_MAX, args=arguments)


def add_market_price(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'market_price' column in USD: mid of bid and ask, converted from BTC."""
    df = df.copy()
    mid_price_btc = (df["bid_price"] + df["ask_price"]) / 2
    df["market_price"] = mid_price_btc * df["underlying_price"]
    return df


def add_implied_volatility(
    df: pd.DataFrame, price_column: str = "market_price", r: float = RISK_FREE_RATE
) -> pd.DataFrame:
    """Add an 'implied_vol' column, inverting the prices in 'price_column'."""
    df = df.copy()

    volatilities = []  # one implied volatility per option

    for i in range(len(df)):
        # take the values of row number i
        price = df[price_column].iloc[i]
        s = df["underlying_price"].iloc[i]
        k = df["strike"].iloc[i]
        T = df["time_to_maturity"].iloc[i]
        option_type = df["option_type"].iloc[i]

        sigma = implied_volatility(price, s, k, r, T, option_type)
        volatilities.append(sigma)

    df["implied_vol"] = volatilities
    return df


def compare_with_deribit(df: pd.DataFrame) -> float:
    """Return the average absolute difference from Deribit's mark IV, in volatility points."""
    difference = df["implied_vol"] * 100 - df["mark_iv"]
    return difference.abs().mean()


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
    df = add_market_price(df)

    # test: inverting the BS prices (built from mark_iv) must give back mark_iv
    test_df = add_black_scholes_price(df)
    test_df = add_implied_volatility(test_df, price_column="bs_price")
    print("Round trip error in volatility points:", compare_with_deribit(test_df))

    # core code: invert the market prices
    df = add_implied_volatility(df, price_column="market_price")
    print("Difference from Deribit IV, vol points:", compare_with_deribit(df))
    print(df[["strike", "option_type", "time_to_maturity", "mark_iv", "implied_vol"]])
