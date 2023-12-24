import matplotlib
import requests as req
import pandas as pd
import numpy as np
# import urllib.request as req
# https://blog.csdn.net/weixin_42213622/article/details/105852794
import os
import json
from datetime import datetime
import pytz

matplotlib.use('Agg')  # 畫完圖不顯示
import matplotlib.pyplot as plt

path, filename = os.path.split(os.path.abspath(__file__))  # 當前路徑及py檔名
save_file_dir = path + "/"

"""
https://candle.etoro.com/candles/asc.json/OneHour/480/100000
https://candle.etoro.com/candles/asc.json/OneHour/480/100000
https://candle.etoro.com/candles/desc.json/OneDay/50/3246
**imp**https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments**imp**
"""


#
# {
#     Interval: "OneDay",
#     Candles: [
#         {
#             InstrumentId: 1,
#             Candles: [
#                 {
#                     InstrumentID: 1,
#                     FromDate: "2022-11-04T00:00:00Z",
#                     Open: 0.97458,
#                     High: 0.99663,
#                     Low: 0.97423,
#                     Close: 0.99625
#                 },
#                 {
#                     InstrumentID: 1,
#                     FromDate: "2022-11-03T00:00:00Z",
#                     Open: 0.98146,
#                     High: 0.98393,
#                     Low: 0.97299,
#                     Close: 0.97455
#                 }
#             ],
#             RangeOpen: 0.97458,
#             RangeClose: 0.97455,
#             RangeHigh: 0.99663,
#             RangeLow: 0.97299
#         }
#     ]
# }


# 這是為了整理etoro格式寫的，for OneDay，for 50筆
def get_price_etoro(i, candle:int=50, thread_number: str = ""):
    url = "https://candle.etoro.com/candles/desc.json/OneDay/" + str(candle) + "/%s" % i
    print(url)
    r_data = req.get(url).text
    # print(url + " get")
    # print("------------------------------------------------------")
    # print(r.headers["content-type"])發現這也是json
    front_key = "Candles"
    price_list = json.loads(r_data)[front_key][0][front_key]
    json_string = json.dumps(price_list)
    output = open(save_file_dir + 'etoro_price/' + thread_number + "_spliced_dict.txt", mode="w")
    output.write(json_string)
    output.close()


# 這是為了把json變成matrix
def etoro_to_matrix(i, thread_number: str = ""):
    x = open(save_file_dir + 'etoro_price/' + thread_number + "_spliced_dict.txt", mode="r")
    # output1=open(Save_file_dir+'etoro_price/'+"_matrix.txt"%i,mode="w")
    xr = json.loads(x.read())
    Date = []
    Open = []
    High = []
    Low = []
    Close = []
    for i in range(len(xr)):  # len(x)可以知道list有幾個i
        Date.append(xr[-i - 1]['FromDate'][0:10])
        # 指第i個list裡的FromDate元素，因為不需要分秒資訊所以只切0~10出來
        Open.append(xr[-i - 1]['Open'])
        # -i-1是因為etoro的資料是最新排到最舊，畫圖的時候要最舊排到最新
        High.append(xr[-i - 1]['High'])
        Low.append(xr[-i - 1]['Low'])
        Close.append(xr[-i - 1]['Close'])
    date_x = pd.DataFrame(Date).rename(columns={0: 'Date'})
    open_x = pd.DataFrame(Open).rename(columns={0: 'Open'})
    high_x = pd.DataFrame(High).rename(columns={0: 'High'})
    low_x = pd.DataFrame(Low).rename(columns={0: 'Low'})
    close_x = pd.DataFrame(Close).rename(columns={0: 'Close'})
    frames = [date_x, open_x, high_x, low_x, close_x]
    fin = pd.concat(frames, axis=1, join='inner')
    # print(fin)
    return fin


# 這是為了畫sma
def sma(data, window):
    # sma = data.rolling(window=window).mean()
    sma = np.round(data.rolling(window=window).mean(), 5)  # 第二位
    # sma = data.rolling(window).mean()這樣寫似乎也可
    return sma


# 這是為了畫bb(20日) 取3個標準差，代表99.7%的樣本會在裡面
def bb(data, sma, window, bb_rang: int):
    std = data.rolling(window=window).std()
    upper_bb = np.round(sma + std * bb_rang, 5)  # 第二位
    lower_bb = np.round(sma - std * bb_rang, 5)  # 第二位
    return upper_bb, lower_bb


# 這是為了回測
def implement_bb_strategy(data, lower_bb, upper_bb):
    buy_price = []
    sell_price = []
    bb_signal = []
    signal = 0
    for i in range(len(data)):
        if data[i - 1] > lower_bb[i - 1] and data[i] < lower_bb[i]:
            if signal != 1:
                buy_price.append(data[i])
                sell_price.append(np.nan)
                signal = 1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        elif data[i - 1] < upper_bb[i - 1] and data[i] > upper_bb[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(data[i])
                signal = -1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            bb_signal.append(0)
    return buy_price, sell_price, bb_signal


def create_file_path():
    try:
        os.mkdir(save_file_dir + 'etoro_price')
    except FileExistsError:
        pass
    try:
        os.mkdir(save_file_dir + 'etoro_price/' + 'png')
    except FileExistsError:
        pass


def pretreat_data_before_draw_bb_plot(ticker_name, ticker_num, thread_number, bb_range: int):
    # 資料前處理

    # name = thread_number  # 同檔案覆寫
    name = ticker_name  # 每個ticker各一個檔案

    get_price_etoro(ticker_num,50, thread_number)
    ticker_matrix = etoro_to_matrix(ticker_num, thread_number)
    duration = ticker_matrix.set_index('Date')

    ticker_fine_matrix = duration
    ticker_fine_matrix["SMA"] = sma(ticker_fine_matrix["Close"], 20)
    ticker_fine_matrix['upper_bb'], ticker_fine_matrix['lower_bb'] = bb(ticker_fine_matrix['Close'],
                                                                        ticker_fine_matrix['SMA'], 20, bb_range)
    buy_price, sell_price, bb_signal = implement_bb_strategy(ticker_fine_matrix['Close'],
                                                             ticker_fine_matrix['lower_bb'],
                                                             ticker_fine_matrix['upper_bb'])

    ticker_fine_matrix["bb_signal"]=bb_signal
    ticker_fine_matrix["buy_price"]=buy_price
    ticker_fine_matrix["sell_price"]=sell_price

    # 落到布林外的，才考慮去存檔
    if (ticker_fine_matrix['upper_bb'][-1] < ticker_fine_matrix['Close'][-1]) or (
                ticker_fine_matrix['lower_bb'][-1] > ticker_fine_matrix['Close'][-1]):
        ticker_fine_matrix.to_csv(save_file_dir + 'etoro_price/' + str(name) + "_fine.csv")
        return True

    return False


def draw_bb_strategy_plot(tickerName):
    try:
        ticker_fine_matrix = pd.read_csv(save_file_dir + 'etoro_price/' + '%s' % tickerName + "_fine.csv").set_index('Date')
    except:
        return
    # 落到布林外的，請考慮交易
    if (ticker_fine_matrix['upper_bb'][-1] < ticker_fine_matrix['Close'][-1]) or (
            ticker_fine_matrix['lower_bb'][-1] > ticker_fine_matrix['Close'][-1]):
        if ticker_fine_matrix['Close'].size < 10:  # 檢查有資料但圖片還是產不出來的情況
            return False
        # 接著畫圖
        ticker_fine_matrix['Close'].plot(label='CLOSE PRICES', alpha=0.3)
        ticker_fine_matrix['upper_bb'].plot(label='UPPER BB', linestyle='--', linewidth=1, color='black')
        ticker_fine_matrix['SMA'].plot(label='MIDDLE BB', linestyle='--', linewidth=1.2, color='grey')
        ticker_fine_matrix['lower_bb'].plot(label='LOWER BB', linestyle='--', linewidth=1, color='black')
        plt.scatter(ticker_fine_matrix.index, ticker_fine_matrix['buy_price'], marker='^', color='green', label='BUY', s=200)
        plt.scatter(ticker_fine_matrix.index, ticker_fine_matrix['sell_price'], marker='v', color='red', label='SELL', s=200)
        plt.title('%s BB STRATEGY TRADING SIGNALS' % tickerName)
        plt.legend(loc='upper left')
        plt.savefig(save_file_dir + 'etoro_price/' + 'png/' + '%s_BBplot' % tickerName)
        # print(ticker_fine_matrix)
        # print("------------------------------------------------------")
        # 記得清畫板
        plt.cla()
        # print("success")
        return True
    else:
        # 因為要上線，所以沒過的就不畫了
        return False


"""
    # ticker = ['27', '28', '29', '1002', '1003', '18', '3025', '3246', '3163', '3306',
    #           '4465', '4459', '3008', '1467', '45', '63', '1111', '3006', '1951',
    #           '5968', '1588', '93', '6357', '3024', '3019', '4269', '3004', '1118',
    #           '2316', '4463', '4251', '100000']
    # nameList = ['spx500', 'nsdq100', 'dj30', 'goog', 'fb', 'gold', 'gld', 'uvxy', 'vix',
    #             'qqq', 'tqqq', 'sqqq', 'xle', 'gs', 'usd_cnh', 'usd_mxn', 'tsla', 'ma',
    #             'swn', 'tdoc', 'x', 'cotton', 'smh', 'xly', 'xli', 'iwd', 'xlf', 'brk_b',
    #             '2318_hk', 'soxx', 'isrg', 'btc']
"""

def make_num_ticker_list(num_ticker_dict):
    ticker = list()
    nameList = list()
    num_ticker = num_ticker_dict
    # ['100073,STORJ', '100074,ZRX', '100075,CELO', '100076,SUSHI', '100077,QNT', '100078,BAL', '100079,FET',
    # '100080,SHIBxM', '100081,AMP', '100082,AXS']
    for i in num_ticker:
        ticker.append(i.split(",")[0])
        nameList.append(i.split(",")[1])
    return ticker,nameList


def out_put_log(watchListToday,failList):
    if len(failList) > 0:
        print("failList:", failList)
    tw = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw).strftime("%Y-%m-%d,%H:%M:%S")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if len(watchListToday) > 0:
        print("請考慮交易:", watchListToday)
        if os.getenv('DEPLOY_SITE') != 'heroku':
            with open(dir_path + "\\flask.log", mode="a") as log:
                log.write(now + "： 請考慮交易:" + str(watchListToday) + " \n")
    # else:
    #     if os.getenv('DEPLOY_SITE') != 'heroku':
    #         print("本日不建議交易")
    #         with open(dir_path+"\\flask.log", mode="a") as log:
    #             log.write(now+"： 本日不建議交易")


def singleton_main(num_ticker_dict, thread_number: str = "", bb_range: int = 3):
    create_file_path()
    ticker, nameList = make_num_ticker_list(num_ticker_dict)
    
    failList = []
    watchListToday = []
    print(f'------------開始運行：{num_ticker_dict}------------')
    for i, j in zip(ticker, range(0, len(ticker))):
        try:
            pretreat_data_before_draw_bb_plot(nameList[j], i, thread_number, bb_range)
            
            result=draw_bb_strategy_plot(nameList[j])
            if result:
                watchListToday.append(nameList[j])
        except Exception as e:
            print(nameList[j])
            print(e)
            failList.append(nameList[j])
            pass
        
    out_put_log(watchListToday,failList)

    return watchListToday


# 減小顆粒度
def singleton_bb_csv_module(ticker_name, ticker_num, thread_number, bb_range: int):
    create_file_path()
    return pretreat_data_before_draw_bb_plot(ticker_name, ticker_num, thread_number, bb_range)
    

# 減小顆粒度
def singleton_bb_plot_module(tickerName):
    create_file_path()
    return draw_bb_strategy_plot(tickerName)


# 減小顆粒度
def singleton_bb_log_module(watchListToday,failList):
    out_put_log(watchListToday,failList)


if __name__ == '__main__':
    singleton_main()
