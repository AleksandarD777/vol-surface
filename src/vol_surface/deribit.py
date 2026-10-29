import requests

BASE_URL = "https://www.deribit.com/api/v2"


def get_instruments(currency: str, kind: str = "option") -> list[dict]:
    """Return all active derivatives instruments for a currency e.g. "BTC"."""
    params = {"currency": currency, "kind": kind, "expired": "false"}
    return _get_deribit_results("get_instruments", params=params)


def get_book_summary_by_currency(currency: str, kind: str = "option") -> list[dict]:
    """Return the book summary for all instruments of a currency.

    Includes open interest, 24h volume, best bid/ask, last price
    and mark IV, filtered by instrument kind.
    """
    params = {
        "currency": currency,
        "kind": kind,
    }
    return _get_deribit_results("get_book_summary_by_currency", params=params)


def _get_deribit_results(endpoint: str, params: dict) -> list[dict]:
    """Send a GET request to a public Deribit endpoint and return its result."""
    url = f"{BASE_URL}/public/{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["result"]


if __name__ == "__main__":
    instruments = get_instruments("BTC", "option")
    print(instruments[0])

    book_summary = get_book_summary_by_currency("BTC", "option")
    print(book_summary[0])
