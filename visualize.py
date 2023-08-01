import json
import bitmex
import requests
import csv
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime


# Connect to the bitmex API
client = bitmex.bitmex()

# Define the BitMEX historical data URL
url = 'https://www.bitmex.com/api/v1/trade/bucketed'

# Set the query parameters
symbol = 'XBTUSD'
bin_size = '1h'
count = 200
time_format = "%H"

params = {
    'symbol': symbol,
    'binSize': bin_size,
    'count': count,
    'reverse': True,
}

# Send the API request to fetch historical data
response = requests.get(url, params=params)
data = response.json()

# Extract the OHLCV data from the response
candles = data

# Define the file path to save the data
csv_file_path = 'bitmex_data.csv'

# Save the data to a CSV file
with open(csv_file_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    for candle in candles:
        writer.writerow([candle['timestamp'], candle['open'], candle['high'], candle['low'], candle['close'], candle['volume']])

# Take the data from the csv file
bitcoin_data = pd.read_csv(csv_file_path,index_col=0,parse_dates=True)
bitcoin_data.index.name = 'Date'

# Plot the price
mpf.plot(bitcoin_data,type='candle',show_nontrading=True,volume=True,style='binance')