import os
import requests
from datetime import datetime
import pytz
import socket


def main(ticker_id):
    hostname = socket.gethostname()
    tw = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw).strftime("%H:%M:%S")
    # https: // www.youtube.com / watch?v = NYT1KFE1X2o
    TOKEN = "5495772446:AAGcdNXEy5BbBo-QGxLcALw2HV-__mrcqlo"
    CHATID = "-1001423405758"
    path, filename = os.path.split(os.path.abspath(__file__))  # 當前路徑及py檔名
    save_file_dir = path + "/"
    file_path = save_file_dir + 'etoro_price/' + 'png/' + '%s_BBplot' % ticker_id + ".png"
    # print(file_path)
    # print(file_path)  # C:\Users\kwz50\PycharmProjects\telebot\etoro_price\png
    url = f"https://api.telegram.org/bot{TOKEN}"
    method = "sendPhoto"
    chat_id = CHATID
    files = {'photo': open(file_path, 'rb')}
    resp = requests.post(
        url + '/' + method + '?chat_id=' + chat_id + '&caption=' + ticker_id + ' ' + now + '(server: ' + hostname + ')',
        files=files)
    # 送檔案可以用這個
    # resp = requests.post(url + '/' + 'sendDocument' + '?chat_id=' + chat_id + '&caption=' + ticker_id, files=files)
    if resp.status_code != 200:
        print(str(ticker_id)+':'+str(resp.status_code))
    return resp


if __name__ == '__main__':
    main()
