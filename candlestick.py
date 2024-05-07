import requests as req
import matplotlib.pyplot as plt
from datetime import datetime
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
import matplotlib.ticker as ticker
import io

def formatexpchart(x, pos=None):  # Add pos argument, default to None if not used
    str_num = str(x)
    if 'e' in str_num:
        parts = str_num.split('e')
        base = float(parts[0])
        exponent = int(parts[1].lstrip('-')) 
        x = int(str(base).split('.')[-1]) 
        y = int(str(base).split('.')[-2]) 
        value = str(y) + str(x)
        zeros = exponent - 1 
        formatted_num = "0.0({}){}".format(zeros, value)
        return formatted_num
    else:
        if x >= 0.001:
            formatted_num = "{:.4f}".format(x)
        elif x >= 0.00001:
            formatted_num = "{:.8f}".format(x)
        else:
            formatted_num = str(x)
        return formatted_num
    
def chart(token, per):
    url = "https://tonapi.io/v2/rates/chart"
    headers = {'Accept': 'application/json'}
    paramters = {
        "token": token,
        'currency': 'ton'
    }
    response = req.get(url,  headers=headers, params=paramters)
    
    data = response.json()
    print(data)
    price=[]
    timestamp = []
    for entry in data['points']:
         price.append(float(entry[1]))
         timestamp.append(float(entry[0]))
    
    pricess = []
    opening = []
    highest = []
    lowest = []
    closing = []
    timestamps =[]
    timecompare = 0
    ohlc = []
    # if len(timestamp) < 100:/2e5
    frame = 60 * int(per)
    # print(frame)
    # else:
    #      per = 900
    for i in range(0,len(timestamp)):
        if timestamp[timecompare]-timestamp[i] >= float(frame) or (i == (len(timestamp) -2)):
                pricess = price[timecompare:(i + 1)]
                highest.append(max(pricess))
                lowest.append(min(pricess))
                opening.append(price[timecompare])
                closing.append(price[i])
                timestamps.append(i)
                timecompare = i+1
    # if opening != []:
    #     print(opening)
    #     # print(highest)
    #     # print(lowest)
    #     # print(closing)
    # else:
    #      print(timestamp[0]-timestamp[len(timestamp)-1])
    if opening != []:
        # print(opening)
        opening.reverse()
        highest.reverse()
        lowest.reverse()
        closing.reverse()
        for j in range(0, len(opening)-1):
             data = []
             data.append(j)
             data.append(opening[j])
             data.append(highest[j])
             data.append(lowest[j])
             data.append(closing[j])
             ohlc.append(data)
             
        df1 = pd.DataFrame(ohlc, columns=['t', 'open', 'high', 'low', 'close'])
        rows_to_add = 100 - len(df1)


        df_zeros = pd.DataFrame({
            't': [0] * rows_to_add,
            'open': [0] * rows_to_add,
            'high': [0] * rows_to_add,
            'low': [0] * rows_to_add,
            'close': [0] * rows_to_add,
        })
        ohlc_df = pd.concat([df1, df_zeros], ignore_index=True)
        # print(ohlc_df)
        ohlc_df = ohlc_df.astype(float)

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.set_facecolor('#ffffff')
        candlestick_ohlc(ax, ohlc_df.values, width=0.6, colorup='#ff7400', colordown='#ffde1a', alpha=0.8)
        ax.set_xticks([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        fig.suptitle('')
        ax.grid(True, color='grey', linestyle='-', linewidth=0.5, which='both',alpha=0.5)
        plt.rcParams['text.color'] = 'black'
        fig.tight_layout()
        y_axis = plt.gca().yaxis
        formatter = ticker.FuncFormatter(formatexpchart)
        ax.yaxis.set_major_formatter(formatter)


        y_axis.set_tick_params(colors='#1c1f2b')
        # plt.fig.show()
        buf = io.BytesIO()
    
        plt.savefig(buf, format='png',bbox_inches='tight')
        # plt.show()
        buf.seek(0)
 
        
        return buf

# chart('EQATcUc69sGSCCMSadsVUKdGwM1BMKS-HKCWGPk60xZGgwsK', 60)