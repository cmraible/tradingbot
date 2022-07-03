import datetime
import logging
import math

import pandas as pd
from alpaca_trade_api import REST, TimeFrame
from alpaca_trade_api.stream import Stream


class TradingBot():
    '''An algorithmic trading bot.'''

    def __init__(self, symbol, api_key, secret_key):
        '''Initiate some important variables and load initial data.'''
        # Set instance variables
        self.symbol = symbol
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://paper-api.alpaca.markets' # change this to live url when ready
        self.stream_url = 'wss://stream.data.alpaca.markets/v2/sip'
        # Create api client object that can be accessed from any method
        self.api = REST(key_id=self.api_key, secret_key=self.secret_key, base_url=self.base_url)

    def get_position(self):
        '''Utility to retrieve our current position, or None from the API.''' 
        try:
            position = self.api.get_position(self.symbol)
            return position
        except:
            return None

    async def bar_callback(self, t):
        '''Run on every bar sent via websocket. This contains the meat of the strategy.'''
        timestamp = datetime.datetime.utcfromtimestamp(t.timestamp/1000000000)
        logging.info('Bar received at %s.' % (timestamp))
        logging.info(t)

        # Call the API to determine if we have a position currently or not
        self.position = self.get_position()
        # Call the API to get other account details, like cash on-hand, etc.
        self.account = self.api.get_account()
        # Call the API to get recent bars from the server
        # We could also store recent data in memory which would be faster
        logging.info('Retrieving recent bars for %s.' % (self.symbol))
        bars = self.api.get_bars(self.symbol, TimeFrame.Minute).df
        logging.info('Recent bars received.')

        # Calculate indicators
        bars['sma20'] = bars['close'].rolling(20).mean()
        bars['sma50'] = bars['close'].rolling(50).mean()

        # Set some convenience variables
        close = t.close
        sma20 = bars['sma20'].iloc[-1]
        sma50 = bars['sma50'].iloc[-1]
        prev_sma20 = bars['sma20'].iloc[-2]
        prev_sma50 = bars['sma50'].iloc[-2]

        # If we're not currently in a position...we might sell
        if not self.position:
            # If the sma20 crosses above the sma50, go all-in!
            if sma20 > sma50 and prev_sma20 < prev_sma50:
                # Calculate how many shares to buy
                # A little less than 100% because the API doesn't seem to accept 100%
                cash = float(self.account.cash)
                allin = math.floor((cash/close)*10000*.95) / 10000
                try:
                    logging.info('BUY %.2f %s @ $%.2f' % (allin, self.symbol, close))
                    order = self.api.submit_order(self.symbol, qty=allin, side="buy", type="market")
                except Exception as e:
                    logging.info('Unable to complete order: %s' % (e))
        else:
            # We are currently long
            logging.info(self.position)
            # In case we have multiple strategies running on different symbols
            if self.position.symbol == self.symbol:
                if (sma20 < sma50):
                    try:
                        logging.info('SELL %s @ $%.2f' % (self.symbol, close))
                        order = self.api.submit_order(self.symbol, qty=self.position.qty, side="sell", type="market")
                    except Exception as e:
                        logging.info('Unable to complete order: %s' % e)
    

    def run(self):
        '''Connect to websocket and continuously monitor for messages.'''
        # Create a stream object using api keys and base url
        stream = Stream(self.api_key, self.secret_key, base_url=self.stream_url)
        # Subscribe to minute bars for the symbol passed to this class
        # On every bar, call the self.bar_callback method with the previous bar's data
        stream.subscribe_bars(self.bar_callback, self.symbol)

        logging.info('Opening connection...')
        stream.run()
        logging.info('Connection closed.')