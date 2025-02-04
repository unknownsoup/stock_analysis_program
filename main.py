"""
purpose: stock analysis software that generates ticker analysis pdfs .

Features:
    - Input ticker name and select (crypto/stock) and timeline
    - Output stock data for provided timeline + chart with 30, 60, 90, 120 EMAs + MACD Chart + VWAP Chart +
      recent relevant news w/ a key-point summary and sentiment rating/analysis.
    - Save summary as pdf
    -
"""
import pandas as pd
import requests                          # making API requests
from datetime import date, timedelta     # getting the date
import re                                # regular expressions
from openai import OpenAI                # summarizing articles and providing insights about the data
import matplotlib.pyplot as plt          # graphing n stuff

# Polygon API Key
API_KEY = "n_4memqwrYdyzCYsz2X0fnZ2JbIhpJJS"
BASE_URL = "https://api.polygon.io"

def is_ticker_valid(ticker):
    pattern = r'^[A-Z]{4}$'
    return bool(re.match(pattern, ticker))

def is_real_ticker(ticker):
    url = f"{BASE_URL}/v3/reference/tickers"
    params = {"ticker": ticker, "apiKey": API_KEY}
    response = requests.get(url, params=params)
    return response.status_code == 200 and len(response.json().get('results', [])) > 0

def ema_graphs(df):
    df['EMA_30'] = df['Close'].ewm(span=30, adjust=False).mean()
    df['EMA_60'] = df['Close'].ewm(span=60, adjust=False).mean()
    df['EMA_90'] = df['Close'].ewm(span=90, adjust=False).mean()
    df['EMA_120'] = df['Close'].ewm(span=120, adjust=False).mean()

    ema_lst = [df['EMA_30'], df['EMA_60'], df['EMA_90'], df['EMA_120']]

    days = 30
    for ema in ema_lst:
        plt.figure(figsize=(12, 6))
        plt.plot(df['DateTime'], df['Close'], label='Close Price')
        plt.plot(df['DateTime'], ema, label=f'{days} EMA', linestyle='--')
        plt.title(f'{symbol} Price with {days} EMA')
        plt.legend()
        days += 30
    plt.show()

current_date = date.today()
SWITCH = True
while SWITCH == True:
    while True:
        symbol = input("Enter a stock ticker (e.g., AAPL, MSFT): ").strip().upper()

        if is_ticker_valid(symbol):
            if is_real_ticker(symbol):
                print(f"'{symbol}: Valid \n")
                break
            else:
                print(f"Ticker '{symbol}' does not exist, try again: ")
        else:
            print("Invalid ticker format, try again: ")

    from_date = current_date - timedelta(days=120)
    to_date = date.today()

    ''' use this to adjust what gets pulled from the URL
    https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to
    '''
    url = (f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}?"
           f"adjusted=true&sort=asc&apiKey=n_4memqwrYdyzCYsz2X0fnZ2JbIhpJJS")

    params = {
        "adjusted": "true",   # Adjusted for splits/dividends
        "sort": "asc",        # Sort data in ascending order
        "limit": 500000,      # Max number of results (adjust as needed)
        "apiKey": API_KEY
    }

    # Send request
    response = requests.get(url, params=params)
    data = response.json()

    # DF formatting
    df = pd.DataFrame(data['results'])
    df['t'] = pd.to_datetime(df['t'], unit='ms')
    df = df.rename(columns={
        'v': 'Volume',
        'vw': 'Vol Weighted Avg Price',
        'o': 'Open',
        'c': 'Close',
        'h': 'High',
        'l': 'Low',
        't': 'DateTime',
        'n': 'Transactions'
    })
    print(df.head(7))
    ema_graphs(df)


    # Prompt to continue or quit
    try:
        choice = input("\n\nComplete!\n"
                       "[1] Enter Another Ticker\n"
                       "[2] Quit\n\n")
        choice = int(choice)

        if choice == 1:
            continue
        elif choice == 2:
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    except ValueError:
        print("Invalid input. Please enter a number (1 or 2).")

print("\nProgram Closed")
