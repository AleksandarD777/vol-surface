import requests

BASE_URL = "https://www.deribit.com/api/v2"

def get_instruments(currency: str, kind: str = "option") -> list[dict]:
    """Return all active derivatives (option if not specified) 
    instruments for a currency e.g. "BTC". """
    
    url = f"{BASE_URL}/public/get_instruments"
    params = {
        "currency": currency,
        "kind": kind,
        "expired": "false"
    } 
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(data.keys())
    return data["result"]

if __name__ == "__main__":
    instruments = get_instruments("BTC", "option")
    print(instruments[0])