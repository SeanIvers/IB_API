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
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close])

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
            self.figures.append(go.Scatter(x=self.df['datetime'], y=self.df[f'{arg} EMA']))

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
    app.reqHistoricalData(1, app.contract, '', '14 D', '5 mins', 'BID', 1, 1, False, [])
    time.sleep(5)
    df = pd.DataFrame(app.data, columns=['datetime', 'open', 'high', 'low', 'close'])
    print(df.size)
    chart = Candlestick(df)
    chart.show_chart()
    app.disconnect()
