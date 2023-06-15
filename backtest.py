import backtrader as bt
import requests
import csv

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.sma_periodo = 20
        self.ema_periodo = 21

        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.sma_periodo)
        self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.ema_periodo)

    def next(self):
        if self.data.close[-1] > self.sma[0] and self.data.close[-2] < self.ema[-2]:
            # Buy signal
            self.buy()
        elif self.data.close[-1] < self.ema[0] and self.data.close[-2] > self.sma[-2]:
            # Sell signal
            self.sell()

# Define the BitMEX historical data URL
url = 'https://www.bitmex.com/api/v1/trade/bucketed'

# Set the query parameters
symbol = 'XBTUSD'
bin_size = '1h'
count = 200

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
    writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
    for candle in candles:
        writer.writerow([candle['timestamp'], candle['open'], candle['high'], candle['low'], candle['close'], candle['volume']])

# Create a cerebro instance
cerebro = bt.Cerebro()

# Create a data feed
data_feed = bt.feeds.GenericCSVData(
    dataname=csv_file_path,
    dtformat='%Y-%m-%dT%H:%M:%S.000Z',  # Format of the datetime column in the CSV file
    datetime=0,  # Column index of the datetime column
    open=1,  # Column index of the open price column
    high=2,  # Column index of the high price column
    low=3,  # Column index of the low price column
    close=4,  # Column index of the close price column
    volume=5,  # Column index of the volume column
    openinterest=-1,  # Column index of the open interest column (-1 if not available)
    timeframe=bt.TimeFrame.Minutes,  # Set the timeframe (Minutes, Days, etc.)
)

# Add the data feed to cerebro
cerebro.adddata(data_feed)

# Add your strategy to cerebro
cerebro.addstrategy(MyStrategy)

# Set the initial capital
initial_capital = 1000.0
cerebro.broker.setcash(initial_capital)

# Set the position size (e.g., 1% of available capital)
position_size = initial_capital * 0.01

# Set the commission scheme (if applicable)
cerebro.broker.setcommission(commission=0.02)

# Run the backtest
cerebro.run()

# Get the final portfolio value
final_value = cerebro.broker.getvalue()

# Print the final portfolio value
print('Final Portfolio Value: {:.2f}'.format(final_value))
