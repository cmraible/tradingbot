import logging
import os
from TradingBot import TradingBot

# Setup a log handler to format our logs more legibly
logging.basicConfig(handlers=[
        # logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ], format='%(asctime)s %(message)s', level=logging.INFO)

# Grab API keys from environment
alpaca_api_key = os.environ.get('APAC_API_KEY_ID')
alpaca_api_secret_key = os.environ.get('APAC_API_SECRET_KEY')

# Create instance of our trading bot and run it!
bot = TradingBot(symbol='AAPL', api_key=alpaca_api_key, secret_key=alpaca_api_secret_key)
bot.run()