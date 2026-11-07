import pandas as pd
from datetime import datetime, timezone, timedelta
from vol_surface.market_data import filter_illiquid_options, run_surface_data_pipeline


def test_filter_keeps_options_at_or_above_min_days():

    # Arrange
    df = pd.DataFrame(
        {
            "time_to_maturity": [6 / 365, 7 / 365, 8 / 365],
            "bid_price": [1, 1, 1],
            "ask_price": [1, 1, 1],
        }
    )

    # Act
    result = filter_illiquid_options(df, min_days=7)

    # Assert
    assert result["time_to_maturity"].tolist() == [7 / 365, 8 / 365]


def test_filter_keeps_options_with_both_bid_ask():

    # Arrange
    df = pd.DataFrame(
        {
            "time_to_maturity": [8 / 365, 8 / 365, 8 / 365, 8 / 365],
            "bid_price": [None, 1, 1, None],
            "ask_price": [1, None, 1, None],
        }
    )

    # Act
    result = filter_illiquid_options(df, min_days=7)

    # Assert
    assert result.index.tolist() == [2]


def test_filter_works_in_pipeline():

    # Arrange
    min_days = 10
    current_dt = datetime.now(timezone.utc)
    tdelta = timedelta(days=min_days)

    def convert_sec_to_ms(expiry: datetime):
        return expiry.timestamp() / 1000

    instruments = [
        {
            "instrument_name": "a",
            "expiration_timestamp": convert_sec_to_ms(current_dt + tdelta),
            "strike": 90.0,
            "option_type": "call",
        },
        {
            "instrument_name": "b",
            "expiration_timestamp": convert_sec_to_ms(current_dt + 2 * tdelta),
            "strike": 90,
            "option_type": "call",
        },
        {
            "instrument_name": "c",
            "expiration_timestamp": convert_sec_to_ms(current_dt + 3 * tdelta),
            "strike": 90.0,
            "option_type": "call",
        },
    ]

    book_summary = [
        {
            "instrument_name": "a",
            "mark_iv": 20,
            "underlying_price": 80,
            "bid_price": 1,
            "ask_price": 1,
        },
        {
            "instrument_name": "b",
            "mark_iv": 20,
            "underlying_price": 80,
            "bid_price": 1,
            "ask_price": 1,
        },
        {
            "instrument_name": "c",
            "mark_iv": 20,
            "underlying_price": 80,
            "bid_price": 1,
            "ask_price": 1,
        },
    ]

    # Act
    results = run_surface_data_pipeline(
        instruments, book_summary, filter_illiquid=True, min_days=min_days
    )

    # Assert
    assert results.index.tolist() == [2]
