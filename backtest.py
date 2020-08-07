import metodos as mtds
import pandas as pd
import numpy as np
import datetime as dt

usdtList = mtds.lista_crypto()
#usdtList = usdtList.head(5)
filename = 'BTCUSDT-15m-data.csv'
inicio = dt.datetime.timestamp(dt.datetime(2020, 4, 1)) * 1000
timestamp = pd.read_csv(filename)
mask = (timestamp['timestamp'] > inicio)
timestamp = timestamp[mask]
timestamp = timestamp.timestamp
kline_size = '15m'
dict = {}
min_RSI = 30
acceptable_rent = 0.7
count_trades = 0
usdtmax = 325+280+400
volumen_average_range = 40
failed = 0
usdt = 30

symbol_list = {}
for symbol in usdtList['symbol']:
    filename = '%s-%s-data.csv' % (symbol, kline_size)
    df = pd.DataFrame(pd.read_csv(filename))
    df["RSI"] = mtds.RSI(14, df)
    df['RSI_14'] = df['RSI']
    df['RSI'] = mtds.RSI(2, df)
    df = df.dropna()
    df.set_index(df['timestamp'], inplace=True)
    symbol_list[symbol] = df

for i in timestamp:
    hour = i
    for j in usdtList['symbol']:
        try:
            last_RSI_14 = symbol_list[j].loc[i]['RSI_14']
            last_RSI_2 = symbol_list[j].loc[i]['RSI']

            if last_RSI_14 < min_RSI:
                jara = 4

            if last_RSI_14 < min_RSI and 2.2 < last_RSI_2 < 20: # and mtds.volume(volumen,volumen_average_range,hora,volume_avg_multiple):



                if mtds.verify_buying_conditions(j, dict, i):

                    if usdtmax - usdt > 0:

                        if not j in dict.keys():
                            dict[j] = []

                        precio = symbol_list[j].loc[i]['close']
                        count_trades += 1
                        dict[j].append([count_trades])
                        entries = len(dict[j])

                        dict[j][entries-1].extend([precio, round(usdt/precio,8), usdt, last_RSI_14, hour, acceptable_rent, 1])
                        usdtmax = usdtmax - usdt
                    else:
                        failed += 1


            if mtds.open_positions(j,dict):
                actual_trade_list, actual_trade_index = mtds.actual_trade(j,dict)

                if not i == actual_trade_list[5]:

                    act_buy = actual_trade_list[1]
                    pb_sell = symbol_list[j].loc[i]['close'] + 0.5*(symbol_list[j].loc[i]['high'] - symbol_list[j].loc[i]['close'])
                    pb_fop = mtds.rent(pb_sell,act_buy)
                    current_acceptable_rent = actual_trade_list[6]

                    if pb_fop > current_acceptable_rent:
                        q_sell = actual_trade_list[2]
                        pc = acceptable_rent
                        sp = actual_trade_list[1]*(1+pc/100)
                        susdt=q_sell*sp
                        ganancia = susdt-actual_trade_list[3]
                        fee = ((susdt+actual_trade_list[3])/2)*0.15/100

                        dict[j][actual_trade_index][7]=0
                        dict[j][actual_trade_index].extend([1,sp, susdt, pc - 0.15, ganancia-fee])
                        usdtmax = usdtmax + susdt
                        print(usdtmax)
        except:
            pass


dff = mtds.series_to_df(dict)
dff['bhour'] = pd.to_datetime(dff['bhour'], unit='ms')
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
#dff['delta'] = (dff['shour']-dff['bhour']).dt.total_seconds()/60
print(dff['fop'].sum())
print(sum(dff['open']))

#print(dff['fop'].sum()/usdtmax*100)

#df['RSI_14'] = df['RSI']

#df = mtds.RSI(2,df)
#df['RSI_2'] = df['RSI']
#df = mtds.RSI(3,df)

#df = mtds.cmf(df,100)
#df = mtds.efi(df,100)

#start = dt.datetime(2019,7,5)
#end = dt.datetime(2019,8,20)

#mask = (df['timestamp']>start)&(df['timestamp']<=end)

#partial = df.loc[mask]
#df.to_csv('test.csv')