import json
import time
from bitmex import bitmex
import pandas as pd
import talib
import requests
import datetime
import csv

global check_venta, check_compra, available_BTC, opening_time, ordersell, orderbuy, price

# Load the BitMex API credentials from the config file
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_key']
api_secret = config['api_secret']

# Connect to the BitMex API
client = bitmex(test=True, api_key=api_key, api_secret=api_secret)

# Define the trading symbol and time interval
symbol = 'XBTUSD'
interval = '1h'
sma_periodo = 20
ema_periodo = 21

# Define the order variables
buyOpen = False
sellOpen = False
limitCompra = False
limitVenta = False
buySignal = False
sellSignal = False

# Archivo csv
csv_path = 'orders.csv'

# Definir el encabezado
header = ['Order ID', 'Fecha Open', 'Ticker', 'Order Type', 'Order Size', 'Price Open', 'Price Closed', 'Comision',
          'Fecha Cierre',
          'Profit/Loss']

# Esta creado o no el csv
try:
    with open(csv_path, 'r') as f:
        pass
except FileNotFoundError:
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)


# Definir la funcion que añade al csv
def add_order_to_csv(order_id, opening_time, ticker, order_type, order_size, price_open, price_closed, comision,
                     closing_time,
                     profit_loss):
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(
            [order_id, opening_time, ticker, order_type, order_size, price_open, price_closed, comision, closing_time,
             profit_loss])

vela_duration = 3600
while True:
    try:
        # Get historical candlestick data from the BitMex API
        candles = client.Trade.Trade_getBucketed(symbol=symbol, binSize=interval, count=200, reverse=True).result()[0]

        # Convert the candlestick data to a pandas DataFrame
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Define the strategy indicators
        df['sma'] = talib.SMA(df['close'], sma_periodo)
        df['ema'] = talib.EMA(df['close'], ema_periodo)

        df['bmsb_mayor'] = df['sma'].where(df['sma'] > df['ema'], other=df['ema'])
        df['bmsb_menor'] = df['ema'].where(df['sma'] >= df['ema'], other=df['sma'])

        last_close = df['close'].iloc[-2]
        bmsb_mayor = df['bmsb_mayor'].iloc[-2]
        bmsb_menor = df['bmsb_menor'].iloc[-2]
        previous_close = df['close'].iloc[-3]
        previous_bmsb_mayor = df['bmsb_mayor'].iloc[-3]
        previous_bmsb_menor = df['bmsb_menor'].iloc[-3]

        print('Last Close: ', last_close)
        print('BMSB Mayor: ', bmsb_mayor)
        print('BMSB Menor: ', bmsb_menor)
        print('Previous Close: ', previous_close)
        print('Previous BMSB Mayor: ', previous_bmsb_mayor)
        print('Previous BMSB Menor: ', previous_bmsb_menor)

        if last_close > bmsb_mayor and previous_close < previous_bmsb_menor:
            buySignal = True
            sellSignal = False
        elif last_close < bmsb_menor and previous_close > previous_bmsb_mayor:
            sellSignal = True
            buySignal = False
        else:
            buySignal = False
            sellSignal = False

        if sellSignal and not buyOpen:
            if sellOpen:
                client.Order.Order_cancelAll(symbol=symbol).result()
                sellOpen = False

            orderSize = round(available_BTC * 0.99, 4)
            order_sell = client.Order.Order_new(symbol=symbol, orderQty=-orderSize, ordType='Market').result()[0]

            ordersell = order_sell['orderID']
            opening_time = datetime.datetime.now()

            while order_sell['ordStatus'] != 'Filled':
                time.sleep(1)
                order_sell = client.Order.Order_getOrders(symbol=symbol, filter=json.dumps({'orderID': ordersell}),
                                                          reverse=True).result()[0][0]
                print('Order ID: ', order_sell['orderID'])
                print('Status: ', order_sell['ordStatus'])

            order_sell_price = order_sell['avgPx']
            commission_sell = order_sell['commission']
            closing_time = datetime.datetime.now()
            profit_loss = round((order_sell_price - price) * orderSize, 2)
            print('Order ID: ', order_sell['orderID'])
            print('Opening Time: ', opening_time)
            print('Ticker: ', symbol)
            print('Order Type: Sell')
            print('Order Size: ', -orderSize)
            print('Price Open: ', price)
            print('Price Closed: ', order_sell_price)
            print('Commission: ', commission_sell)
            print('Closing Time: ', closing_time)
            print('Profit/Loss: ', profit_loss)
            add_order_to_csv(order_sell['orderID'], opening_time, symbol, 'Sell', -orderSize, price, order_sell_price,
                             commission_sell, closing_time, profit_loss)
            sellOpen = False

        elif buySignal and not sellOpen:
            if buyOpen:
                client.Order.Order_cancelAll(symbol=symbol).result()
                buyOpen = False

            orderSize = round(available_BTC * 0.99, 4)
            order_buy = client.Order.Order_new(symbol=symbol, orderQty=orderSize, ordType='Market').result()[0]

            orderbuy = order_buy['orderID']
            opening_time = datetime.datetime.now()

            while order_buy['ordStatus'] != 'Filled':
                time.sleep(1)
                order_buy = client.Order.Order_getOrders(symbol=symbol, filter=json.dumps({'orderID': orderbuy}),
                                                         reverse=True).result()[0][0]
                print('Order ID: ', order_buy['orderID'])
                print('Status: ', order_buy['ordStatus'])

            order_buy_price = order_buy['avgPx']
            commission_buy = order_buy['commission']
            closing_time = datetime.datetime.now()
            profit_loss = round((order_buy_price - price) * orderSize, 2)
            print('Order ID: ', order_buy['orderID'])
            print('Opening Time: ', opening_time)
            print('Ticker: ', symbol)
            print('Order Type: Buy')
            print('Order Size: ', orderSize)
            print('Price Open: ', price)
            print('Price Closed: ', order_buy_price)
            print('Commission: ', commission_buy)
            print('Closing Time: ', closing_time)
            print('Profit/Loss: ', profit_loss)
            add_order_to_csv(order_buy['orderID'], opening_time, symbol, 'Buy', orderSize, price, order_buy_price,
                             commission_buy, closing_time, profit_loss)
            buyOpen = False

    except Exception as e:
        print(e)

    time.sleep(vela_duration)
