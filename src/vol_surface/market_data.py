import pandas as pd
from vol_surface.deribit import get_book_summary_by_currency, get_instruments


def merge_market_data(
    instruments: list[dict], book_summary_by_currency: list[dict]
) -> pd.DataFrame:
    """Join instruments with their book summaries, keeping only instruments present in both."""
        
    df_inst = pd.DataFrame(instruments)
    df_book = pd.DataFrame(book_summary_by_currency)
    df = pd.merge(df_inst, df_book, how="inner", on="instrument_name")
    return df


if __name__ == "__main__":
    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    df = merge_market_data(instruments, book_summary_by_currency)

    print(df.columns)
