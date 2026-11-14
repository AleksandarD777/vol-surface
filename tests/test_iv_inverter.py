import numpy as np
import pandas as pd
import pytest

from vol_surface.iv_inverter import add_implied_vol, bs_price, implied_vol


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("sigma", [0.1, 0.4, 1.2])
def test_implied_vol_recovers_sigma(option_type, sigma):
    price = bs_price(S=100, K=110, r=0.0, sigma=sigma, T=0.5, option_type=option_type)
    result = implied_vol(
        S=100, K=110, r=0.0, T=0.5, price=price, option_type=option_type
    )
    assert result == pytest.approx(sigma, abs=1e-6)


def test_implied_vol_returns_nan_outside_bounds():
    # A call cannot be worth more than the underlying
    result = implied_vol(S=100, K=100, r=0.0, T=1.0, price=150.0, option_type="call")
    assert np.isnan(result)


def test_implied_vol_rejects_unknown_option_type():
    with pytest.raises(ValueError):
        implied_vol(S=100, K=100, r=0.0, T=1.0, price=5.0, option_type="straddle")


def test_add_implied_vol_handles_missing_quotes():
    sigma = 0.5
    price_usd = bs_price(S=100, K=100, r=0.0, sigma=sigma, T=0.25, option_type="call")
    df = pd.DataFrame(
        {
            "underlying_price": [100.0, 100.0],
            "strike": [100.0, 100.0],
            "time_to_maturity": [0.25, 0.25],
            "option_type": ["call", "call"],
            "bid_price": [price_usd / 100, 0.0],
            "ask_price": [price_usd / 100, 0.0],
        }
    )

    result = add_implied_vol(df)

    assert result["implied_vol"].iloc[0] == pytest.approx(sigma, abs=1e-6)
    assert np.isnan(result["implied_vol"].iloc[1])