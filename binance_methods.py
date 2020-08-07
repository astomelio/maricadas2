from binance.client import Client
import pandas as pd
from datetime import datetime
import os.path
import math
import decimal
# import keys
import metodos as mtds
# from sendTGM import telegram_bot_sendtext
import numpy as np

client = Client(api_key="eURnxpA5QOm2c2Y7tXxwCbyyVTG5jUaOii67GfIz4FEOgzQ0SLQjgf0uoWZDynVe", api_secret="XsqSfKPRZaJYBcn36mm5FKYF2dzIuRxikbI6TbSJuREc3XItWlRW0rn7IAoa3Zmm")

#ROUNDUP

def round_up(n, decimals=0):
    multiplier = 10 ** decimals

    
    return math.ceil(n * multiplier) / multiplier

#CALCULA CANTIDAD DE COMPRA DE LA MONEDA ACORDE A UN USDT APROXIMADO A GASTAR

def asset_info_min_Buy(symbol):
    info = client.get_symbol_info(symbol)
    USD_min = 50 #float(info['filters'][3]['minNotional'])
    last_price = client.get_all_tickers()
    symbol_LP = float(list(filter(lambda last_price: last_price['symbol'] == symbol, last_price))[0]['price'])
    precision = abs(decimal.Decimal(str(float(info['filters'][2]['stepSize']))).as_tuple().exponent)
    Q_buy = USD_min / symbol_LP
    coins_available = Q_buy
    ticks = {}
    for filt in info['filters']:
        if filt['filterType'] == 'LOT_SIZE':
            ticks[symbol] = filt['stepSize'].find('1') - 2
            break
    order_quantity = math.ceil(coins_available * 10 * ticks[symbol]) / float(10 * ticks[symbol])
    return order_quantity, order_quantity*symbol_LP

#COMPRA EFECTIVA DE LA MONEDA

def buy_order(symbol,quantity):
    order_buy = client.order_market_buy(symbol=symbol, quantity=quantity)
    usdt = float(order_buy['cummulativeQuoteQty'])
    close = float(order_buy['fills'][0]['price'])
    time = float(order_buy['transactTime'])
    return usdt, close, time

def format_float(num):
    return np.format_float_positional(num, trim='-')

#VENTA EFECTIVA DE LA MONEDA

def sell_order(symbol,quantity):
    order_sell = client.order_market_sell(symbol=symbol, quantity=quantity)
    close = float(order_sell['fills'][0]['price'])  # PRECIO DE VENTA
    time = float(order_sell['transactTime'])
    utilty = quantity*close
    return close, utilty, time

def sell_limit_order(symbol,quantity,price):
    correct_price = symbol_price_precision(symbol,price)
    order_sell = client.order_limit_sell(symbol=symbol,quantity=quantity,price = str(correct_price))
    #close = float(order_sell['fills'][0]['price'])  # PRECIO DE VENTA
    #time = float(order_sell['transactTime'])
    #utilty = quantity * close
    order_id = order_sell['orderId']

    return order_id,correct_price

def symbol_price_precision(symbol,sell_price):
    info = client.get_symbol_info(symbol)
    for filt in info['filters']:
        if filt['filterType'] == 'PRICE_FILTER':
            h = filt['tickSize'].find('1') - 1
            break
    correct_price = round_up(sell_price, h)
    correct_price = format_float(correct_price)
    return correct_price


def buy_order_test(symbol,quantity):
    close = last_price(symbol)
    usdt=quantity *close
    time = datetime.now().timestamp()*1000
    return usdt, close, time

#VENTA EFECTIVA DE LA MONEDA

def sell_order_test(symbol,quantity):
    close = last_price(symbol)
    utilty = quantity*close
    time = datetime.now().timestamp()*1000
    return close, utilty, time

# CALCULA CANTIDAD LIBRE DE MONEDA EN ESPECIFICO

def free_quantity(symbol):
    return float(client.get_asset_balance(asset=symbol)['free'])

#PRECIO ACTUAL DE LA MONEDA

def last_price(symbol):
    last_price = client.get_all_tickers()
    symbol_LP = float(list(filter(lambda last_price: last_price['symbol'] == symbol, last_price))[0]['price'])
    return symbol_LP

#RETORNA DF HISTORICO DE LA MONEDA

def klines(symbol,kline_size):
    filename = '%s-%s-data.csv' % (symbol, kline_size)
    if os.path.isfile(filename):
        exists = True
        data_prev = pd.read_csv(filename)
        inicio = int(data_prev['timestamp'].iloc[-1])
        data_prev.drop(data_prev.tail(1).index, inplace=True)

    else:
        exists = False
        inicio = int((datetime(2017, 1, 1).timestamp()))
    print('Downloading '+symbol + '....')
    klines = client.get_historical_klines(symbol,kline_size,inicio)
    new_data = pd.DataFrame(klines,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                 'quote_av','trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    print('Finished!')
    if exists:
        data = data_prev
        data = data.append(new_data)
    else:
        data = new_data

    data.to_csv(filename, index = False)
    data = pd.read_csv(filename)

    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    return data

def id_info(symbol,id):
    order = client.get_order(symbol=symbol,orderId = str(id))
    i = float(order['origQty'])
    f = float(order['executedQty'])
    if f-i == 0:
        return 0
    else:
        return 1

def act_dict(dict):
    closed = []
    for keys in dict:
        for rows in dict[keys]:
            if rows[7]== 1:
                if id_info(keys,rows[8]) == 0:
                    rows[7] = id_info(keys,rows[8])
                    par = [keys]
                    par.append(rows[12])
                    closed.append(par)

    if not len(closed)==0:
        df = pd.DataFrame(closed, columns=['coin','USDT'])
        df = df.set_index('coin')
        telegram_bot_sendtext('Positions Closed:')
        telegram_bot_sendtext(str(df))

        suma = total_fop(dict)

        msg = 'Total USDT: '+str(round(suma,4))
        telegram_bot_sendtext(msg)

        open = mtds.open_symbols(dict)
        if not len(open)==0:
            telegram_bot_sendtext('Open Positions on:')
            telegram_bot_sendtext(str(open))
        else:
            telegram_bot_sendtext('No Open Position')

def total_fop(dict):
    suma = 0
    for keys in dict:
        for row in dict[keys]:
            if row[7]==0:
                suma += row[12]

    return sum

def act_list():
    list = pd.DataFrame([sub['symbol'] for sub in client.get_exchange_info()['symbols']])
    usdt = list[list[0].str.contains('USDT')]
    usdt.to_csv('ListaUSDT.csv')


for symbol in usdtList['symbol']:
    klines(symbol,'15m')