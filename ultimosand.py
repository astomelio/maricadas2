import pandas as pd
import binance_methods as bm
import datetime as dt
import metodos as mtds
import time as tm
from sendTGM import telegram_bot_sendtext
import sys


### DECLARAR VARIABLES

cerrar_prg_bool = True  # BOOLEANO QUE DETERMINA SI QUIERE FINALIZAR EL PROGRAMA O NO. ACTUALIZAR EN EL ARCHIVO _CSV_CONTINUE.CSV
resumen_trades_dict = mtds.load_pickle()  # DICCIONARIO CON EL RESUMEN DE LOS TRADES
trades_df = mtds.series_to_df(resumen_trades_dict)
min_RSI_14 = 30  # MINIMO RSI 14 PARA COMPRA DE MONEDA
min_RSI_2 = 2.2
max_RSI_2 = 20
count_loops = 0  # CANTIDAD DE ITERACIONES REALIZADAS
count_trades = len(trades_df)  # CANTIDAD DE TRADES TOTALES
failed_trades = 0  # CANTIDAD DE TRADES FALLIDOS POR FALTA DE RECUROS
acceptable_rent = 0.65  #RENTABILIDAD MINIMA ACEPTADA PARA CERRAR TRADE
resumen = []
I_BNB = bm.free_quantity('BNB') #BNB INICIAL DISPONIBLE EN LA CUENTA
Inicial = bm.free_quantity('USDT')  # USDT INICIAL DISPONIBLE EN LA CUENTA
Max = Inicial  # USD RESTANTE PARA TRADES. INICIA CON EL VALOR INICIAL
usdtList = mtds.lista_crypto() # LEE LISTA DE USDT A ITERAR
dict_symbol_kline = {}

print('Se inicia corrida con ' + str(Inicial) + ' USDT')  # IMPRIME USD INICIAL

print('Loading klines')

for i in usdtList['symbol']:
    dict_symbol_kline[i] = bm.klines(i,'15m')

print('Finished')
while cerrar_prg_bool:  # REVISA SI SE DESEA PARAR EL PROGRAMA Y SI TODAVIA HAY POSICIONES ABIERTAS

    count_loops += 1  # CALCULO DE ITERACIONES TOTALES

    for i in usdtList.index:  # ITERA LA LISTA DE MONEDAS

        try:
            bm.act_dict(resumen_trades_dict) #ACTUALIZA BASE, MANDA MENSAJE DE LAS POSICIONES CERRADAS Y ABIERTAS
        except:
            tm.sleep(30)
            bm.act_dict(resumen_trades_dict)  # ACTUALIZA BASE, MANDA MENSAJE DE LAS POSICIONES CERRADAS Y ABIERTAS

        trades_df = mtds.series_to_df(resumen_trades_dict)

        mtds.save_pickle(resumen_trades_dict)

        #--------------------------INICIO ACTUALIZACIÓN DE RSI---------------------------------

        symbol = str(usdtList['symbol'][i])  # MONEDA ACTUAL DE LA ITERACIÓN

        df_ant = dict_symbol_kline[symbol]
        dict_symbol_kline[symbol] = bm.klines_df(symbol, '15m',df_ant)  # ACTUALIZA KLINE DE LA MONEDA ACTUAL

        df = dict_symbol_kline[symbol].tail(150)

        rsi_14 = mtds.RSI(14, df)  # CALCULA EL INDICADOR RSI 14
        rsi_02 = mtds.RSI(2, df) # CALCULA EL INDICADOR RSI 2
        last_RSI_14 = rsi_14.iloc[-1]  # ULTIMO RSI DE LA MONEDA ACTUAL
        last_RSI_2 = rsi_02.iloc[-1]  # ULTIMO RSI DE LA MONEDA ACTUAL

        print('RSI ' + str(round(last_RSI_14, 2)) + ' - ' + str(round(last_RSI_2, 2)))  # PRINT ULTIMO RSI PARA INFORMACIÓN

        #------------------------FIN ACTUALIZACIÓN DE RSI---------------------------------

        #---------------------------INICIO COMPRA DE LA MONEDA----------------------------

        if last_RSI_14 < min_RSI_14 and min_RSI_2 < last_RSI_2 < max_RSI_2:  # REVISA SI RSI ACTUAL ES MENOR AL RSI MINIMO PARA COMPRA

            last_price = bm.last_price(symbol)

            if mtds.verify_buying_conditions(symbol, resumen_trades_dict,dt.datetime.now().timestamp()*1000,last_price) and cerrar_prg_bool:  # PARA COMPRAR DEBE SER BOOLEANO FALSE Y NO TENER UNA
                # POSICIÓN ABIERTA CON ESA MONEDA

                qbuy_act, usdtmin_act = bm.asset_info_min_Buy(symbol)  # CANTIDAD MINIMA DE VENTA Y SU EQUIVALENTE APROXIMADO DE USDT

                Max = bm.free_quantity('USDT')  # RECALCULA CANTIDAD RESTANTE DE USDT EN LA CUENTA

                if Max - usdtmin_act > 0:  # VERIFICA SI HAY RECURSOS DISPONIBLES EN LA CUENTA

                    if not symbol in resumen_trades_dict:  # SI NO EXISTE TRADE ANTERIOR DE LA MONEDA CREA UNA NUEVA ENTRADA EN EL DICCIONARIO
                        resumen_trades_dict[symbol] = []  # CREA NUEVA ENTRADA VACIA EN EL DICCIONARIO

                    usdt_b, bp, time = bm.buy_order(symbol, qbuy_act)  # COMPRA MONEDA

                    msg = 'BUYING ' + str(round(usdt_b, 2)) + ' USDT OF ' + str(
                        symbol) + ' NOW AT ' + str(
                        bp) + ' WITH RSI OF ' + str(round(last_RSI_14, 2)) + '%'

                    telegram_bot_sendtext(msg)  # ENVIA CORREO DE LA COMPRA REALIZADA

                    sell_price = bp * (1 + acceptable_rent / 100)

                    order_id,sp = bm.sell_limit_order(symbol,qbuy_act,sell_price)

                    count_trades += 1  # AGREGA UNO A LAS POSICIONES TOTALES
                    ## AGREGA MONEDA, VALOR DE COMPRA, CANTIDAD COMPRADA DE LA MONEDA, CANTIDAD COMPRADA EN USDT, RSI y HORA DE COMPRA

                    resumen_trades_dict[symbol].append([count_trades])
                    entries = len(resumen_trades_dict[symbol])
                    sp = float(sp)
                    pc = mtds.rent(sp, bp)
                    usdt_s = sp*qbuy_act
                    fop = round(usdt_s - usdt_b, 5)

                    resumen_trades_dict[symbol][entries - 1].extend(
                        [bp, qbuy_act, usdt_b, last_RSI_14, time, acceptable_rent, 1, order_id,sp,usdt_s,pc-0.15,fop])

                    mtds.save_pickle(resumen_trades_dict)

                    ## IMPRIME MENSAJE DE COMPRA

                    print('Resta: ' + str(Max) + 'USDT')  # IMPRIME USDT RESTANTE

                else:  # SI NO HAY SUFICIENTES RECURSOS DOCUMENTARLO EN LA VARIABLE NI
                    failed_trades += 1  # AGREGA UNO A LA VARIABLE


    ### CODIGO PARA MOSTRAR DETALLE E INFORMACIÓN DE CADA ITERACIÓN ####

    print()
    print('////////////// RESULTADOS DEL LOOP ' + str(count_loops) + ' ///////////////////////')
    bm.open_loss(resumen_trades_dict)
    print('_open_loss.csv actualizado')

    #### DETERMINA SI EL PROGRAMA SEGUIRA CORRIENDO O NO.

    if cerrar_prg_bool:
        a = pd.read_csv('_csv_continue.csv')['a'].iloc[0]

    if a == 's':
        cerrar_prg_bool = True
        print('No ha detenido el Script')
    elif a == 'n':
        cerrar_prg_bool = False
        print('Ha detenido el Script.')

    print()

print('Saving klines')

for i in usdtList['symbol']:

    df = dict_symbol_kline[i]
    bm.save_klines(i,'15m',df)

print('Finished')

# todo Si no hay internet, poner un try hasta n cantidad de veces. Depronto un sleep
# todo enviar periodicamente un resumen de la utilidad y de cuanto esta libre y cuanto esta comprometido a Telegram
# todo incluir futures