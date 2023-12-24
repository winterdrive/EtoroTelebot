# Etoro X Telebot 
## What-Can-Trade-Today (run in [Heroku app](https://etorotelebot.herokuapp.com/) and backup with [Railway app](https://etorotelebot-production.up.railway.app/))
### Features：
1. use BB strategy to check tickers
2. BB strategy demo clip is on Google Drive now :
#### Demo Locally
    https://drive.google.com/file/d/1WIVBSOXXoSdfN-0M6hUhFN8FWXoG8EcR/view?usp=sharing
#### Demo in Heroku app with telegram bot
    https://drive.google.com/file/d/1ZQqjkHx6O02Nn7fkRiaDMwwxnQw-4pbd/view?usp=sharing
#### Demo screenshot on mobile device
<img src="https://github.com/winterdrive/EtoroTelebot/blob/master/static/images/screenshot1.jpg" width="480" alt="screenshot1">
<img src="https://github.com/winterdrive/EtoroTelebot/blob/master/static/images/screenshot2.jpg" width="480" alt="screenshot2">


#### subscribing the channel
<img src="https://github.com/winterdrive/EtoroTelebot/blob/master/static/images/channelQRCODE.png" width="300" height="400" alt="screenshot3">



## 效能提升
### 2022/11/06 in localhost
- V1 
  - 條件：4845個ticker, ticker number in each batch=10, thread number=1, bb std=2, 
  - 結果：~=***90分鐘(600張圖)***
  - 未來改善方向：
    1. 太慢，需提速
- V2 
  - 條件：4845個ticker, ticker number in each batch=10, thread number=3, bb std=2,
  - 結果：~=***47分鐘(600張圖)***，圖片異常，resp:429
  - 更新項目：
    - [x] thread number=1，改為多執行續thread number=3處理
  - 未來改善方向：
    1. matplotlib非線程安全，所以會有Race Condition，圖片才會異常，須逐個製圖(by queue or list)
        - https://matplotlib.org/3.1.0/faq/howto_faq.html?fbclid=IwAR3RjWyVS2fjFR9iLRiZvpfVcuQhPewDX3JK8ndRFDG7RwKqqoZ0FYzdVZM#working-with-threads
    2. telegram 會擋過於頻繁的request(resp:429)，須穩定依次發圖
- V3
  - 條件：4845個ticker, ticker number in batch=100, thread number=5, bb std=3,
  - 結果： ~=***15分鐘(50張圖)***
  - 更新項目：
    - [x] std=2條件過於寬鬆，更改為std=3
    - [x] 429及製圖缺失大量減少，因為每批次執行數量提升，且bb std拉高，需製作及傳送的圖已大量減少，但仍需使用queue使系統更robust
  - 未來改善方向：
    1. 多主機併行衍生議題
    2. 多執行續衍生議題
    3. 資料處理過程的中繼檔案過多

### 2022/11/07 in localhost connect remote redis
- V4 
  - 條件：4845個ticker, ticker number in batch=100, thread number=5, bb std=3,
  - 結果：~=***27分鐘(不含發圖)***，時間拉長，因為Redis連線次數增加
  - 更新項目：
    - [x] 重構資料處理流程，減少中繼檔案數量
    - [x] 製圖模組重構，解決多執行續下的資源競爭問題
    - [x] 發圖模組重構，以便後續處理resp:429問題
    - [x] 多主機任務分派(免費版只執行選定ticker，自己的主機再執行所有ticker)
        - railway測試，單次花費
        - ENVIRONMENT參數決定哪台主機是master哪台主機是slave
  - 未來改善方向： 
    1. redis操作提速

### 2022/11/08 in localhost connect remote redis with LUA script
- V5
  - 條件：4845個ticker, ticker number in batch=100, thread number=5, bb std=3, LUA script     
  - 更新項目：
    - [x] Lua腳本處理狀態值改變(111->999)，減少連線次數，並保證atomic，避免多執行續交互存取產生的髒資料
    - [x] redis連線測試，查尋及修改 in 100 loop
      1. 每個動作都取一次連線(100次連線後查詢+4845次連線後更新)：~300s
      2. 取一次連線後執行查及改(1次連線+100次查詢+4845次更新)：46s~91s
      3. 取一次連線後送LUA腳本(100次連線後執行LUA腳本)：1s~5s
  - 結果：~=***19分鐘(12張圖)***，
  - 未來改善方向：
    1. 檢驗多主機執行時redis是否需上鎖
        - https://developer.aliyun.com/article/677797
        - https://blog.csdn.net/weixin_41754309/article/details/121419465
        - https://cloud.tencent.com/developer/article/1574207
        - https://zhuanlan.zhihu.com/p/112016634
        - https://zhuanlan.zhihu.com/p/258890196
    2. 極小化本機檔案儲存量，最好能只存圖不存csv


<br>
<hr>

## Auto-Login-and-Buy (developing)
###### Etoro frequently changes their UI/UX, so it might not work now
### Features：
1. auto login your Etoro account
2. switch to virtual portfolio
3. open positions
#### Demo Locally
    https://drive.google.com/file/d/1a5LGwJYYAsmHQJFpWiJyKPtz2ni_J-fg/view?usp=sharing

## Possible Features in the Future (if I'm not busy)
1. create a main page
2. open position with a click 
3. close position with a click 
4. check positions with a click
