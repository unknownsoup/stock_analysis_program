"""
purpose: stock analysis software that generates ticker analysis pdfs.

Features:
    - Input ticker name and select (crypto/stock) and timeline
    - Output stock data for provided timeline + chart with 30, 60, 90, 120 EMAs + MACD Chart + VWAP Chart +
      recent relevant news w/ a key-point summary and sentiment rating/analysis.
    - Save summary as pdf
    -
"""
import pandas as pd
import requests                                         # making API requests
from datetime import date, timedelta                    # getting the date
import re                                               # regular expressions
from openai import OpenAI                               # summarizing articles and providing insights about the data
import matplotlib.pyplot as plt                         # graphing n stuff
from matplotlib.backends.backend_pdf import PdfPages    # saving graphs to pdf

# Polygon API Key
API_KEY = "YOUR KEY"
BASE_URL = "https://api.polygon.io"

# checking if the user inputted ticker is in the correct format
def is_ticker_valid(ticker):
    pattern = r'^[A-Z]{4}$'
    return bool(re.match(pattern, ticker))

# checking if that same ticker exists
def is_real_ticker(ticker):
    url = f"{BASE_URL}/v3/reference/tickers"
    params = {"ticker": ticker, "apiKey": API_KEY}
    response = requests.get(url, params=params)
    return response.status_code == 200 and len(response.json().get('results', [])) > 0

# creating the 30, 60, 90, and 120 Moving Average charts
def ema_graphs(df, pdf=None):
    df['EMA_30'] = df['Close'].ewm(span=30, adjust=False).mean()
    df['EMA_60'] = df['Close'].ewm(span=60, adjust=False).mean()
    df['EMA_90'] = df['Close'].ewm(span=90, adjust=False).mean()
    df['EMA_120'] = df['Close'].ewm(span=120, adjust=False).mean()

    # Plotting Close Price + All EMAs
    plt.figure(figsize=(14, 8))

    # Plot Close Price
    plt.plot(df['DateTime'], df['Close'], label='Close Price', linewidth=2, color='black')

    # Plot EMAs
    plt.plot(df['DateTime'], df['EMA_30'], label='30 EMA', linestyle='--', color='blue')
    plt.plot(df['DateTime'], df['EMA_60'], label='60 EMA', linestyle='--', color='orange')
    plt.plot(df['DateTime'], df['EMA_90'], label='90 EMA', linestyle='--', color='green')
    plt.plot(df['DateTime'], df['EMA_120'], label='120 EMA', linestyle='--', color='red')

    # Graph Aesthetics
    plt.title(f'{symbol} Price with 30, 60, 90, 120 EMAs')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)

    if pdf:
        pdf.savefig()  # Save the current figure to PDF
        plt.close()  # Close the figure after saving
    else:
        plt.show()

    # creating the MACD and VWAP charts
def MACD_VWAP_chart(df, pdf=None):
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    # VWAP Calculation
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['Cumulative_TPV'] = (df['Typical_Price'] * df['Volume']).cumsum()
    df['Cumulative_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cumulative_TPV'] / df['Cumulative_Volume']

    # Plotting
    plt.figure(figsize=(14, 8))

    # Price and VWAP
    plt.subplot(2, 1, 1)
    plt.plot(df['DateTime'], df['Close'], label='Close Price', color='blue')
    plt.plot(df['DateTime'], df['VWAP'], label='VWAP', linestyle='--', color='orange')
    plt.title(f'{symbol} - Close Price with VWAP')
    plt.legend()

    # MACD and Signal Line
    plt.subplot(2, 1, 2)
    plt.plot(df['DateTime'], df['MACD'], label='MACD', color='green')
    plt.plot(df['DateTime'], df['Signal_Line'], label='Signal Line', linestyle='--', color='red')
    plt.bar(df['DateTime'], df['MACD_Hist'], label='MACD Histogram', color='gray', alpha=0.4)
    plt.title(f'{symbol} - MACD Indicator')
    plt.legend()

    plt.tight_layout()

    if pdf:
        pdf.savefig()  # Save the current figure to PDF
        plt.close()  # Close the figure after saving
    else:
        plt.show()

SWITCH = True
while SWITCH == True:
    # grabbing ticker from the user
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

    # getting the da
    to_date = date.today()
    from_date = to_date - timedelta(days=120)

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
    ema_graphs(df=df)
    MACD_VWAP_chart(df=df)

    # Menu to enter again, save as pdf, or quit
    try:
        choice = input("\n\nComplete!\n"
                       "[1] Enter Another Ticker\n"
                       "[2] Save to PDF and Quit\n"
                       "[3] Quit\n\n")
        choice = int(choice)

        if choice == 1:
            continue
        elif choice == 2:
            pdf_filename = f"{to_date}_{symbol}_Charts.pdf"
            with PdfPages(pdf_filename) as pdf:
                ema_graphs(df=df, pdf=pdf)
                MACD_VWAP_chart(df=df, pdf=pdf)
                break
        elif choice == 3:
            break
        else:
            print("Invalid choice. Please enter 1-3: ")
    except ValueError:
        print("Invalid input. Please enter a number (1-3): ")

print("Program Closed")
