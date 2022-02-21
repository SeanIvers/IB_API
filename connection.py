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
        # Only use on one day
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

    def remove_time(self, market_time):
        # Remove time before market hour
        # Format = hh:mm
        # DO THIS FIRST!
        df_list = self.df.values.tolist()
        indx_market_time = []
        new_df_list = []
        end_time = '15:55'
        index_end_time = []
        for i in df_list:
            if i[0][-8:-3] == market_time:
                indx = df_list.index(i)
                break
        new_df_list = df_list[indx:]
        for i in df_list:
            if i[0][-8:-3] == end_time:
                index_end_time.append(new_df_list.index(i))
            if i[0][-8:-3] == market_time:
                indx = df_list.index(i)
                indx_market_time.append(new_df_list.index(i))
        newer_df_list = []
        for a, b in zip(indx_market_time, index_end_time):
            for i in range(a, b + 1):
                newer_df_list.append(new_df_list[i])
        new_df = pd.DataFrame(data=newer_df_list, columns=self.df.columns)
        self.df = new_df
        self.figures[0] = go.Candlestick(x=self.df['datetime'], open=self.df['open'], high=self.df['high'], low=self.df['low'], close=self.df['close'])

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
    app.reqHistoricalData(1, app.contract, '20220214 16:00:00', '1 D', '5 mins', 'TRADES', 1, 1, False, [])
    time.sleep(5)
    df = pd.DataFrame(app.data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    chart = Candlestick(df)
    chart.remove_time('10:00')
    chart.add_EMA(7, 20, 200)
    chart.add_VWAP()
    chart.show_chart()
    app.disconnect()
