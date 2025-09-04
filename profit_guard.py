# profit_guard.py
# Live queries for profitability.

import requests

def get_doge_price():
    try:
        # Using CoinGecko API
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=dogecoin&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        return data['dogecoin']['usd']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DOGE price from CoinGecko: {e}")
        return None
    except KeyError:
        print("Unexpected JSON structure from CoinGecko API.")
        print("Response content:")
        print(response.text)
        return None

def get_doge_difficulty():
    try:
        # Using Blockchair API
        response = requests.get("https://api.blockchair.com/dogecoin/stats")
        response.raise_for_status()
        data = response.json()
        return data['data']['difficulty']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DOGE difficulty from Blockchair: {e}")
        return None
    except KeyError:
        print("Unexpected JSON structure from Blockchair API.")
        print("Response content:")
        print(response.text)
        return None

if __name__ == "__main__":
    print("Running Profit Guard check...")
    price = get_doge_price()
    difficulty = get_doge_difficulty()

    if price and difficulty:
        print(f"Current DOGE price: ${price:.4f}")
        print(f"Current DOGE difficulty: {difficulty}")
