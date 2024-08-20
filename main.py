import pyupbit
import time
from datetime import datetime
from pytz import timezone
import pandas as pd
import telegram
import json
from dotenv import load_dotenv
import os

# 함수 정의
def cal_target(ticker):
    df_cal_target = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df_cal_target.iloc[-2]
    today = df_cal_target.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    target = today['open'] + yesterday_range * 0.5
    return target

def sell(ticker):
    balance = upbit.get_balance(ticker)
    s = upbit.sell_market_order(ticker, balance)
    msg = f"{ticker} 매도 시도\n{json.dumps(s, ensure_ascii=False)}"
    print(msg)
    bot.sendMessage(mc, msg)

def buy(ticker, money):
    b = upbit.buy_market_order(ticker, money)
    if 'error' in b:
        b = upbit.buy_market_order(ticker, 100000)
        msg = f"돈 좀 부족해서 {ticker} 100000원 매수 시도\n{json.dumps(b, ensure_ascii=False)}"
    else:
        msg = f"{ticker} {money}원 매수 시도\n{json.dumps(b, ensure_ascii=False)}"
    print(msg)
    bot.sendMessage(mc, msg)

def printall():
    msg = f"------------------------------{now.strftime('%Y-%m-%d %H:%M:%S')}------------------------------\n"
    for i in range(n):
        msg += f"{coin_list[i]:>10} 목표가: {target[i]:>11.1f} 현재가: {prices[i]:>11.1f} 매수금액: {money_list[i]:>7} hold: {str(hold[i]):>5} status: {op_mode[i]}\n"
    print(msg)
    bot.sendMessage(mc, msg)

def save_data(krw_balance):
    own_coin_list_04_08 = [0, 0, 0]  # BTC, ETH, DOGE
    df_saved_data = pd.read_csv('saved_data.csv')
    now_prices = [-1] * n
    jonbeo = "----------들고만 있었으면----------\n"
    total_jonbeo = 0
    auto_upbit = f"----------자동화----------\n자동화 총 금액 -> {krw_balance}\n"
    
    for i in range(n):
        now_prices[i] = pyupbit.get_current_price(coin_list[i])
        total_jonbeo += now_prices[i] * own_coin_list_04_08[i]
        jonbeo += f"{coin_list[i]} 현 가격: {now_prices[i]} 이 코인의 총 가격 {now_prices[i] * own_coin_list_04_08[i]}\n"
        time.sleep(0.1)

    jonbeo += f"지금까지 존버했으면 총 금액 -> {total_jonbeo}\n"
    msg = f"{jonbeo}{auto_upbit}존버와의 금액 차이 -> {krw_balance - total_jonbeo}원 벌었음(-이면 잃은거)\n"
    
    try:
        dif_yesterday = krw_balance - df_saved_data.iloc[-1]['auto_upbit']
        msg += f"!!어제와의 금액 차이!!: {dif_yesterday}"
        df2 = pd.DataFrame([{
            'date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'jonbeo': total_jonbeo,
            'auto_upbit': krw_balance,
            'difference_jonbeo_autoupbit': krw_balance - total_jonbeo,
            'difference_yesterday': dif_yesterday
        }])
    except Exception:
        df2 = pd.DataFrame([{
            'date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'jonbeo': total_jonbeo,
            'auto_upbit': krw_balance,
            'difference_jonbeo_autoupbit': krw_balance - total_jonbeo
        }])
        
    df2.to_csv('saved_data.csv', mode='a', header=False, index=False)
    print(msg)
    bot.sendMessage(mc, msg)

def get_yesterday_ma15(ticker):
    df_get_yesterday_ma15 = pyupbit.get_ohlcv(ticker)
    close = df_get_yesterday_ma15['close']
    ma = close.rolling(window=15).mean()
    return ma.iloc[-2]

# 객체 생성
load_dotenv()
access = os.getenv("UPBIT_ACCESS")
secret = os.getenv("UPBIT_SECRET")
upbit = pyupbit.Upbit(access, secret)
token = os.getenv("TELEGRAM_TOKEN")
mc = "@Crypto_expobot"
bot = telegram.Bot(token)
df = pd.read_csv('dataset.csv')

# 변수 설정
coin_list = ["KRW-BTC", "KRW-ETH", "KRW-DOGE"]
n = len(coin_list)
percent_list = [0.05] * n
INF = float('inf')
skip_list = []
money_list = [0] * n
op_mode = [False] * n
hold = [False] * n
target = [INF] * n
prices = [-1] * n
yesterday_ma15 = [0] * n

# 중간에 시작하더라도 target 데이터와 money_list 데이터 op_mode, hold데이터를 로드
for i in range(n):
    target[i] = df.loc[i, 'target']
    money_list[i] = df.loc[i, 'money_list']
    hold[i] = df.loc[i, 'hold']
    op_mode[i] = df.loc[i, 'op_mode']
    yesterday_ma15[i] = df.loc[i, 'yesterday_ma15']
    if coin_list[i] in skip_list:
        op_mode[i] = False
        df.loc[i, 'op_mode'] = False

df.to_csv('dataset.csv', index=False)

# 매매 루프
while True:
    try:
        # 지금 한국 시간
        now = datetime.now(timezone('Asia/Seoul'))
        
        # 하루에 한번 작동하는 save 변수 초기화
        if prev_day != now.day:
            prev_day = now.day
            save1 = save2 = save3 = True
            msg = f"save 변수가 True로 업데이트 됐습니다.\nsave1: {save1}, save2: {save2}, save3: {save3}"
            bot.sendMessage(mc, msg)
        
        # 8시 50분에 코드 실행 확인 메시지 전송
        if now.hour == 8 and now.minute == 50 and save3:
            msg = "코드가 정상 실행 중입니다."
            bot.sendMessage(mc, msg)
            save3 = False

        # 매도 시도
        if now.hour == 8 and now.minute == 59 and save1:
            for i in range(n):
                if hold[i] and op_mode[i]:
                    sell(coin_list[i])
                    hold[i] = op_mode[i] = False
                    df.loc[i, 'hold'] = df.loc[i, 'op_mode'] = False
            
            df.to_csv('dataset.csv', index=False)
            krw_balance = upbit.get_balance("KRW")
            
            for i in range(n):
                money_list[i] = int(krw_balance * percent_list[i])
                df.loc[i, 'money_list'] = money_list[i]
                
            df.to_csv('dataset.csv', index=False)
            msg = f"----------매수할 돈 정보 갱신(money_list)----------\n" + "\n".join([f"{coin} {money}원" for coin, money in zip(coin_list, money_list)])
            print(msg)
            bot.sendMessage(mc, msg)
            save_data(krw_balance)
            save1 = False

        # 09:00:00 목표가 갱신
        if now.hour == 9 and now.minute == 0 and now.second > 30 and save2:
            for i in range(n):
                target[i] = cal_target(coin_list[i])
                op_mode[i] = True
                df.loc[i, 'target'] = target[i]
                df.loc[i, 'op_mode'] = True
                yesterday_ma15[i] = get_yesterday_ma15(coin_list[i])
                df.loc[i, 'yesterday_ma15'] = yesterday_ma15[i]
                if coin_list[i] in skip_list:
                    op_mode[i] = False
                    df.loc[i, 'op_mode'] = False
            
            df.to_csv('dataset.csv', index=False)
            msg = f"----------목표가 갱신(target)----------\n" + "\n".join([f"{coin} {tgt}원" for coin, tgt in zip(coin_list, target)])
            print(msg)
            bot.sendMessage(mc, msg)
            msg = "어제 ma15 가격 갱신\n" + "\n".join([f"{coin} -> {ma15}원" for coin, ma15 in zip(coin_list, yesterday_ma15)])
            
            for i in range(n):
                if yesterday_ma15[i] > target[i]:
                    msg += f"{coin_list[i]}는 yesterday_ma15가 target보다 커서 안 사질 수도 있음 yesterday_ma15 -> {yesterday_ma15[i]} target -> {target[i]}\n"
            
            bot.sendMessage(mc, msg)
            print(msg)
            save2 = False

        # 현 가격 가져오기
        prices = [pyupbit.get_current_price(coin) for coin in coin_list]

        # 매초마다 조건을 확인한 후 매수 시도
        for i in range(n):
            if op_mode[i] and not hold[i] and prices[i] >= target[i] and prices[i] >= yesterday_ma15[i]:
                buy(coin_list[i], money_list[i])
                hold[i] = True
                df.loc[i, 'hold'] = True
                
        df.to_csv('dataset.csv', index=False)
        
        # 상태 출력
        printall()
        
        # 3시간마다 코드 실행 확인 메시지 전송
        if (now.hour % 3) == 0 and time_save:
            time_save = False
            msg = f"지금 {now.hour}시입니다. 코드가 잘 실행되고 있습니다."
            bot.sendMessage(mc, msg)
    
    except Exception as e:
        print(e)
        bot.sendMessage(mc, str(e))
