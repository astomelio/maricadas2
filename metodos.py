import numpy as np
import pandas as pd
import ta.momentum as ta
import ta.volume as tav
import datetime
import pickle

#from pandas.tests.groupby.test_index_as_string import series


def open_trades_list(i, l, df):
    lista = []
    if len(l) != 0:
        for element in l:
            a = df.index[df['symbol'] == element].tolist()[0]
            lista.append(a)
    lista.append(i)
    return lista

def TimeDelta_Boolean(minInt, F_I, F_F):
    if (F_F - F_I).total_seconds() / 60 <= minInt:
        return False
    else:
        return True

def second_buy(nRSI, p_RSI):
    if p_RSI - nRSI > 7:
        return True
    else:
        return False

def RSI(nu, df): #Calcula RSI de un DF. Debe tener el timestamp en columna, no en index

    c = df.close
    rsi = ta.rsi(c,n=nu)
    return rsi

def lista_crypto():
    usdtList = pd.read_csv('ListaUSDT(per).csv')
    usdtList = usdtList[usdtList['seg'] == 'X'].reset_index(drop=True)
    return usdtList




def verify_buying_conditions(symbol, dict,now,last_price):

    hour = []
    price = []
    open = True
    if symbol in dict.keys():
        for rows in dict[symbol]:
            if rows[7] > 0:
                hour.append(rows[5])
                price.append(rows[1])
    try:
        minutes = (now - max(hour))/1000/60
        if minutes < 30:
            open = False
    except:
        open = True


    if len(price) >= 3:

        open = False

    elif not len(price)==0:

        if min(price) < last_price:

            open = False

    return open

def open_positions(symbol, dict):

    open = False
    fin = True
    if symbol in dict.keys():
        for rows in dict[symbol]:
            if rows[7] > 0 and fin:
                open = True
                fin = False
    return open

def actual_trade(symbol,dict):
    p = 100000
    n = -1
    for row in dict[symbol]:
        n +=1
        if row[7] > 0:
            if row[1]<p:
                p = row[1]
                act = row
                index = n
    return act,index

def rent(sell,close):
    return round((sell/close-1)*100,4)

def resumen_df(dict):
    if len(dict) == 0:
        return 'No hay trades cerrados'
    else:
        r_list = []
        for keys in dict:
            for row in dict[keys]:
                if row[7] == 0:
                    r_list.append([keys,row[11],row[12]])
    r_df = pd.DataFrame(r_list,columns=['symbol','rent(%)','rent(USDT'])

    return r_df

def min_rent(dict,delta_rent,hora,delta_hour): # todo revisar esta función
    for key in dict.keys():
        for index in range(0,len(dict[key])):
            if dict[key][index][7] > 0:
                time = pd.to_datetime(dict[key][index][5], unit='ms')
                minutes = (hora-time).total_seconds()/60
                laps = dict[key][index][7]
                if delta_hour*60*laps<minutes:
                    dict[key][index][7] += 1
                    dict[key][index][6] -= delta_rent #(laps)*2

def series_to_df(dict):
    series = []
    for key in dict:
        for row in dict[key]:
            a1 = [key]
            a1.extend(row)
            series.append(a1)

    df = pd.DataFrame(series,columns=['symbol','trade','bp','quantity','busdt','brsi','bhour','min_rent','open','id','sp','susdt','pc','fop'])

    return df

def round_down(num,divisor):
    return num-(num%divisor)

def date_to_minute(hora):
    return hora.minute+hora.second/60

def volume(volume,average_range,time,n):
    volume = volume.reset_index(drop = True)
    act_volume = volume.tail(1).iloc[0]
    avg_unit_volume = volume.head(average_range).mean()/15
    minutes = date_to_minute(time)
    delta = minutes-round_down(minutes,15)
    if delta == 0:
        delta = 15
    act_unit_volume = act_volume/delta

    if act_unit_volume > n*avg_unit_volume:
        return False
    else:
        return True

def cmf(df,number):
    h = df.high
    l = df.low
    c = df.close
    v = df.volume
    cmf = tav.chaikin_money_flow(h,l,c,v,n=number)
    df['cmf'] = cmf
    return df

def eom(df,number):
    h = df.high
    l = df.low
    v = df.volume
    eom = tav.ease_of_movement(h,l,v,n=number)
    df['ease'] = eom
    return df

def efi(df,number):
    c = df.close
    v = df.volume
    efi = tav.force_index(c, v, n=number)
    df['efi'] = efi
    return df

def save_pickle(dict):
    p_out = open('dict.pickle','wb')
    pickle.dump(dict,p_out)
    p_out.close()

def load_pickle():
    p_in = open('dict.pickle','rb')
    dict = pickle.load(p_in)
    return dict

def open_symbols(dict):
    open = []
    for keys in dict:
        for rows in dict[keys]:
            if rows[7] == 1:
                open.append(keys)
                break
    return open

def symbol_market_close():
    open = pd.read_csv('_open_loss.csv')

    try:
        close = open[open['5'] == 'x']['0'].tolist()
    except:
        close = []

    return close