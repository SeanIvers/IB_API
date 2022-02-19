from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import time
import threading
from ibapi.contract import Contract
import pandas as pd
import plotly.graph_objects as go

class IBapi(EWrapper, EClient):
    def __init__(self):
        self.data = []
        self.contract = None
        EClient.__init__(self, self)

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    def createStockContract(self, symbol, exchange):
        self.contract = Contract()
        self.contract.symbol = symbol
        self.contract.secType = 'STK'
        self.contract.exchange = exchange
        self.contract.currency = 'USD'

class Candlestick:
    def __init__(self, df):
        self.df = df
        self.figures = [
            go.Candlestick(x=self.df['datetime'], open=self.df['open'], high=self.df['high'], low=self.df['low'], close=self.df['close'])
        ]

    def add_EMA(self, *args):
        self.ema_list = list(args)
        for arg in self.ema_list:
            self.df[f'{arg} EMA'] = self.df['close'].ewm(span=arg, adjust=False).mean()
            self.figures.append(go.Scatter(name = f'{arg} EMA', x=self.df['datetime'], y=self.df[f'{arg} EMA']))

    def add_VWAP(self):
        price_volume_period = []
        price_volume_cumsum = []
        vwap = []
        sum = 0

        # Add cumulative sum of price * volume for the period
        for i in range(self.df['datetime'].size):
            # pricevolume = (high + low + close) / 3 * volume for the period
            price_volume_period.append(((self.df.iloc[i, 2] + self.df.iloc[i, 3] + self.df.iloc[i, 4]) / 3) * self.df.iloc[i, 5])
            sum += price_volume_period[i]
            price_volume_cumsum.append(sum)

        self.df['CumSumPV'] = price_volume_cumsum
        self.df['CumSumVol'] = self.df['volume'].cumsum()

        for i in range(self.df['datetime'].size):
            vwap.append(price_volume_cumsum[i] / self.df.iloc[i, self.df.columns.get_loc('CumSumVol')])

        self.df['VWAP'] = vwap

        self.figures.append(go.Scatter(name='VWAP', x=self.df['datetime'], y=self.df['VWAP']))

    def show_chart(self):
        fig = go.Figure(
            self.figures
        )
        fig.show()

def run_loop():
    app.run()

if __name__ == '__main__':
    app = IBapi()
    app.connect('127.0.0.1', 4002, 1)
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()
    time.sleep(1)
    app.createStockContract('SPY', 'SMART')
    app.reqHistoricalData(1, app.contract, '', '2 D', '5 mins', 'TRADES', 1, 1, False, [])
    time.sleep(5)
    # print(app.data)
    df = pd.DataFrame(app.data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    # chart = Candlestick(df)
    # chart.add_EMA(20, 7)
    # chart.add_VWAP()
    # chart.show_chart()
    # print(df.head())
    count = 0
    df_list = df.values.tolist()
    # print(df_list)
    market_after_10_list = [x for x in df_list if int(x[0][-8:-6]) >= 10]
    # print(market_after_10_list)
    df_settled = pd.DataFrame(market_after_10_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    print(df_settled.head())
    chart = Candlestick(df_settled)
    chart.add_EMA(7, 20)
    chart.show_chart()
    # Short term moves above long term EMA
    for i in range(df_settled['datetime'].size - 1):
        if i > 0:
            if df_settled.iloc[i, df_settled.columns.get_loc('7 EMA')] < df_settled.iloc[i, df_settled.columns.get_loc('20 EMA')] and df_settled.iloc[i + 1, df_settled.columns.get_loc('7 EMA')] > df_settled.iloc[i + 1, df_settled.columns.get_loc('20 EMA')]:
                count += 1
                print(i)
    print(count)
    app.disconnect()
