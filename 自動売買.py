import pandas as pd
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.endpoints.orders import OrderCreate
import time
import json
#ボリンジャーバンドの幅
sigma = 2
#何秒ごとにデータ観測＆売買判断を行うか
interval_sec = 5
#移動平均の計測期間
duration = 26
#API認証
accountID = input("口座IDを入力してください")
access_token = input("アクセストークンを入力してください")
oanda = API(access_token=access_token, environment="live")
#5秒足の終値を現在価格として使用する
params = {
    "count":1,
    "granularity":"S5"
}
#始めに価格データをただ観測する時の動き
def price_data_collecting(samples=100):
    print("これから約"+str(samples*interval_sec)+"秒間価格データ収集を行います。")
    price_list=[]
    for _ in range(samples):
        #価格データ取得
        r = instruments.InstrumentsCandles(instrument="USD_JPY", params=params)
        price = float(r.response['candles'][1]['mid']["c"])
        price_list.append(price)
        print("現在価格："+str(price))
        time.sleep(interval_sec)
    print("価格データ収集が完了しました。")
    return price_lis
price_list = price_data_collecting()
#ボリンジャーバンド関連の計算はpandasデータフレームを使う
#これを元にオリジナルの自動売買プログラムを作る時は、この辺をいじることになる
df = pd.DataFrame()
df["price"]=price_list
while True:
    #過去為替データを取得
    r = instruments.InstrumentsCandles(instrument="USD_JPY", params=params)
    #現在価格
    price_now = float(r.response['candles'][1]['mid']["c"])
    df=df.append({'price': price_now,}, ignore_index=True)
    #移動平均と標準偏差を計算
    df["MSE"]=df["price"].rolling(window=duration).mean()
    df["std"]=df["price"].rolling(window=duration).std()
    #注目している σ区間の境界線(今回は下にsigma分と上にsigma分、つまりデフォルトで偏差値30以下と70以上)
    df["lower_limit"]=df["MSE"]-sigma*df["std"]
    df["upper_limit"]=df["MSE"]+sigma*df["std"]
    #最新の値段がσ区間を超えているか判定
    #今回はボリンジャーバンドより下なら安すぎる（=ロングすべき）、上なら高すぎる（=ショートすべき）という考え方
    if df.iloc[-1]["price"]<df.iloc[-1]["lower_limit"]:
        print("買い注文(ロングポジション)を実行します。")
        data = {
            "order": {
                "instrument": "USD_JPY",
                "units": 10000,
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
        ep = OrderCreate(accountID=accountID, data=data)
        rsp = oanda.request(ep)
        print(json.dumps(rsp, indent=2))
    elif df.iloc[-1]["price"]>df.iloc[-1]["upper_limit"]:
        print("売り注文(ショートポジション)を実行します。")
        data = {
        "order": {
        "instrument": "USD_JPY",
        "units": -10000,
        "type": "MARKET",
        "positionFill": "DEFAULT"
        }
        }
        ep = OrderCreate(accountID=accountID, data=data)
        rsp = oanda.request(ep)
        print(json.dumps(rsp, indent=2))
    else:
        print("売買はありません。")
    #先頭行を削除してdfの長さを一定に保つ（長時間の運用時のメモリ対策）
    df=df.drop(df.index[0])
    time.sleep(interval_sec)